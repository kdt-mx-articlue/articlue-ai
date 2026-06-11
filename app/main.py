from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI

from app.api.routes.pipeline import (
    router as pipeline_router
)

from app.api.routes.resume_router import (
    router as resume_router
)

# =========================
# FastAPI App
# =========================
app = FastAPI(
    title="AI Pipeline API"
)

# =========================
# Router 등록
# =========================
app.include_router(
    pipeline_router
)

app.include_router(
    resume_router
)