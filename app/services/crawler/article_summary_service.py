import os
import logging
import asyncio
from datetime import datetime, timezone
from app.services.llm.llm_json_service import LlmJsonService
from app.prompts.crawler.summary_prompt import build_summary_prompt, PROMPT_VERSION

logger = logging.getLogger(__name__)
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 모듈 로드 시 1회만 초기화하여 자원 낭비 방지
llm = LlmJsonService()

def _process_single_article(article: dict) -> dict:
    article_id = article.get("id")
    summary_data = None
    
    prompt_data = build_summary_prompt(article)
    
    try:
        llm_response = llm.invoke_json(
            system_prompt=prompt_data["system"], 
            user_prompt=prompt_data["user"]
        )
        summary_data = llm_response.get("summary")
    except Exception as e:
        logger.error(f"[Summary Service] Article {article_id} 요약 실패: {str(e)}")
        
    return {
        "id": article_id,
        "summary": {
            "text": summary_data,
            "model": MODEL_NAME,
            "promptVersion": PROMPT_VERSION,
            "createdAt": datetime.now(timezone.utc).isoformat()
        } if summary_data else None
    }

async def generate_summaries(articles: list[dict]) -> dict:
    tasks = [
        asyncio.to_thread(_process_single_article, article)
        for article in articles
    ]
    
    result_articles = await asyncio.gather(*tasks)
    return {"articles": list(result_articles)}