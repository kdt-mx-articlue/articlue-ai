from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from app.pipeline.service import run_pipeline

router = APIRouter()

# =========================
# In-Memory Job Store
# =========================
JOB_STORE = {}


# =========================
# Request Schema
# =========================
class PipelineRequest(BaseModel):

    json_path: str = Field(
        ...,
        min_length=5,
        description="이력서 JSON 경로"
    )

    resume_id: int = Field(
        ...,
        gt=0,
        description="이력서 ID"
    )


# =========================
# Response Schema
# =========================
class PipelineStatusResponse(BaseModel):

    job_id: str

    status: str

    result: Optional[dict] = None

    error: Optional[str] = None


# =========================
# Background Pipeline
# =========================
def process_pipeline(
    job_id: str,
    json_path: str,
    resume_id: int
):

    try:

        # =========================
        # Pipeline 실행
        # =========================
        result = run_pipeline(
            json_path=json_path,
            resume_id=resume_id
        )

        JOB_STORE[job_id] = {
            "status": "done",
            "result": result
        }

    except Exception as e:

        JOB_STORE[job_id] = {
            "status": "failed",
            "error": str(e)
        }


# =========================
# Pipeline 실행 API
# =========================
@router.post(
    "/pipeline/analyze",
    response_model=PipelineStatusResponse
)
def analyze(
    req: PipelineRequest,
    background_tasks: BackgroundTasks
):

    # =========================
    # Job ID 생성
    # =========================
    job_id = str(uuid.uuid4())

    # =========================
    # 초기 상태 저장
    # =========================
    JOB_STORE[job_id] = {
        "status": "processing"
    }

    # =========================
    # Background Task 등록
    # =========================
    background_tasks.add_task(
        process_pipeline,
        job_id,
        req.json_path,
        req.resume_id
    )

    return {
        "job_id": job_id,
        "status": "processing"
    }


# =========================
# 결과 조회 API
# =========================
@router.get(
    "/pipeline/result/{job_id}",
    response_model=PipelineStatusResponse
)
def get_result(job_id: str):

    job = JOB_STORE.get(job_id)

    if not job:

        raise HTTPException(
            status_code=404,
            detail="job_id not found"
        )

    return {
        "job_id": job_id,
        **job
    }