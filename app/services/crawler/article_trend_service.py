import os
import logging
from datetime import datetime, timezone
from app.services.llm.llm_json_service import LlmJsonService
from app.prompts.crawler.trend_prompt import build_trend_prompt, PROMPT_VERSION

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_ARTICLES = 20

llm = LlmJsonService()

async def generate_trends(articles: list[dict], keywords: dict) -> dict:
    # API 응답 구조 일관성 확보
    if not articles or not keywords:
        return {
            "trends": [],
            "meta": {
                "articleCount": len(articles) if articles else 0,
                "keywordCount": len(keywords) if keywords else 0,
                "model": MODEL_NAME,
                "promptVersion": PROMPT_VERSION,
                "createdAt": datetime.now(timezone.utc).isoformat()
            }
        }

    target_articles = articles[:MAX_ARTICLES]
    prompt_data = build_trend_prompt(target_articles, keywords)
    trend_list = []
    
    try:
        llm_response = llm.invoke_json(
            system_prompt=prompt_data["system"], 
            user_prompt=prompt_data["user"]
        )
        raw_trends = llm_response.get("trends")
        
        if isinstance(raw_trends, list):
            trend_list = raw_trends
        else:
            logger.warning(f"[Trend Service] LLM 응답 'trends'가 list 형식이 아닙니다. 타입: {type(raw_trends)}")

    except Exception as e:
        # 디버깅에 용이한 상세 로그
        logger.error(
            f"[Trend Service] "
            f"articles={len(target_articles)} "
            f"keywords={len(keywords)} "
            f"Error: {e}"
        )
        
    return {
        "trends": trend_list,
        "meta": {
            "articleCount": len(target_articles),
            "keywordCount": len(keywords),
            "model": MODEL_NAME,
            "promptVersion": PROMPT_VERSION,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    }