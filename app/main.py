from fastapi import FastAPI

from app.api.routes.pipeline import router as pipeline_router

app = FastAPI(
    title="AI Pipeline API"
)

# 라우터 등록
app.include_router(pipeline_router)