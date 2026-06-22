import os
import logging
from datetime import datetime, timezone
from app.services.llm.llm_json_service import LlmJsonService
from app.prompts.crawler.prompt_context_prompt import build_prompt_context_prompt, PROMPT_VERSION

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
llm = LlmJsonService()

async def generate_prompt_context(articles: list[dict], trends: list[dict]) -> dict:
    # 데이터가 없을 때의 기본값 스키마 일관성 확보
    if not articles or not trends:
        return {
            "promptContext": {
                "rawText": ""
            },
            "meta": {
                "articleCount": len(articles) if articles else 0,
                "trendCount": len(trends) if trends else 0,
                "length": 0,
                "model": MODEL_NAME,
                "promptVersion": PROMPT_VERSION,
                "createdAt": datetime.now(timezone.utc).isoformat()
            }
        }

    prompt_data = build_prompt_context_prompt(articles, trends)
    context_data = {"rawText": ""} # 기본 구조 보장
    
    try:
        llm_response = llm.invoke_json(
            system_prompt=prompt_data["system"], 
            user_prompt=prompt_data["user"]
        )
        raw_context = llm_response.get("promptContext", {})
        
        if (
            isinstance(raw_context, dict)
            and isinstance(raw_context.get("rawText"), str)
            ):
            context_data = raw_context
        else:
            logger.warning("[Prompt Context Service] LLM 응답 형식이 올바르지 않아 기본값을 사용합니다.")

    except Exception as e:
        logger.error(f"[Prompt Context Service] 컨텍스트 생성 실패: {str(e)}")
        
    return {
        "promptContext": context_data,
        "meta": {
            "articleCount": min(len(articles), 20),
            "trendCount": len(trends),
            "length": len(context_data.get("rawText", "")), # 글자 수 저장
            "model": MODEL_NAME,
            "promptVersion": PROMPT_VERSION,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    }