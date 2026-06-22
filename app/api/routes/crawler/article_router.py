from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional

router = APIRouter(
    prefix="/crawler",
    tags=["Crawler AI"]
)

# ---------------------------------------------------------
# 공통 Pydantic 모델 (Optional 기반 방어적 스키마 설계)
# ---------------------------------------------------------
class ArticleSummary(BaseModel):
    # Node.js에서 에러 객체나 null이 넘어와도 에러가 나지 않도록 유연하게 대처
    text: List[str] = []
    model: Optional[str] = None
    promptVersion: Optional[str] = None
    createdAt: Optional[str] = None
    error: Optional[str] = None

class ArticleInput(BaseModel):
    id: str
    title: str
    body: Optional[str] = None
    summary: Optional[ArticleSummary] = None

class TrendInput(BaseModel):
    trendId: int
    topic: str
    description: str

# ---------------------------------------------------------
# Request 모델
# ---------------------------------------------------------
class SummaryRequest(BaseModel):
    articles: List[ArticleInput]

class KeywordRequest(BaseModel):
    articles: List[ArticleInput]

class TrendRequest(BaseModel):
    articles: List[ArticleInput]
    keywords: Dict[str, int]

class PromptContextRequest(BaseModel):
    articles: List[ArticleInput]
    trends: List[TrendInput]

# ---------------------------------------------------------
# Endpoints (exclude_none=True 패턴 적용)
# ---------------------------------------------------------
from app.services.crawler.article_summary_service import generate_summaries
from app.services.crawler.article_keyword_service import generate_keywords
from app.services.crawler.article_trend_service import generate_trends
from app.services.crawler.prompt_context_service import generate_prompt_context

@router.post("/summary")
async def create_summary(request: SummaryRequest):
    # exclude_none=True를 통해 null/None 필드를 완벽하게 제거한 정제된 dict 리스트 생성
    articles_dict = [
        article.model_dump(exclude_none=True) 
        for article in request.articles
    ]
    return await generate_summaries(articles_dict)

@router.post("/keyword")
async def create_keyword(request: KeywordRequest):
    articles_dict = [
        article.model_dump(exclude_none=True) 
        for article in request.articles
    ]
    return await generate_keywords(articles_dict)

@router.post("/trend")
async def create_trend(request: TrendRequest):
    articles_dict = [
        article.model_dump(exclude_none=True) 
        for article in request.articles
    ]
    keywords_dict = request.keywords
    return await generate_trends(articles_dict, keywords_dict)

@router.post("/prompt-context")
async def create_prompt_context(request: PromptContextRequest):
    articles_dict = [
        article.model_dump(exclude_none=True) 
        for article in request.articles
    ]
    trends_dict = [
        trend.model_dump(exclude_none=True) 
        for trend in request.trends
    ]
    return await generate_prompt_context(articles_dict, trends_dict)