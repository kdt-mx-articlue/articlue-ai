from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services.ranking_service import rank_jobs
from app.pipeline.service import run_pipeline

router = APIRouter()


class PipelineRequest(BaseModel):
    json_path: str
    resume_id: int


# 백그라운드 작업 함수
def process_pipeline(json_path: str, resume_id: int):
    run_pipeline(json_path, resume_id)


@router.post("/pipeline/analyze")
def analyze(req: PipelineRequest, background_tasks: BackgroundTasks):

    background_tasks.add_task(
        process_pipeline,
        req.json_path,
        req.resume_id
    )

    return {
        "status": "processing",
        "message": "pipeline started"
    }