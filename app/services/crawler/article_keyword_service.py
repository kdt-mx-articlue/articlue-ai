import os
import logging
from datetime import datetime, timezone
from app.services.llm.llm_json_service import LlmJsonService
from app.prompts.crawler.keyword_prompt import build_keyword_prompt, PROMPT_VERSION

logger = logging.getLogger(__name__)

# 상수는 최상단으로 분리
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_ARTICLES = 20

llm = LlmJsonService()

async def generate_keywords(articles: list[dict]) -> dict:
    if not articles:
        return {"keywords": {}}

    target_articles = articles[:MAX_ARTICLES]
    prompt_data = build_keyword_prompt(target_articles)
    keyword_map = {}
    
    try:
        llm_response = llm.invoke_json(
            system_prompt=prompt_data["system"], 
            user_prompt=prompt_data["user"]
        )
        raw_keywords = llm_response.get("keywords")
        
        # 실제 dict 타입인지 안전하게 검증
        if isinstance(raw_keywords, dict):
            keyword_map = raw_keywords
        else:
            logger.warning(f"[Keyword Service] LLM 응답 'keywords'가 dict 형식이 아닙니다. 타입: {type(raw_keywords)}")
            keyword_map = {}

    except Exception as e:
        logger.error(f"[Keyword Service] 키워드 추출 실패: {str(e)}")
        
    return {
        "keywords": keyword_map,
        "meta": {
            "articleCount": len(target_articles),
            "model": MODEL_NAME,
            "promptVersion": PROMPT_VERSION,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    }