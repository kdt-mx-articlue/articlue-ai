from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import uuid

from app.pipeline.service import run_pipeline

router = APIRouter()

# 간단 in-memory job store (MVP용)
JOB_STORE = {}


class PipelineRequest(BaseModel):
    json_path: str
    resume_id: int


def process_pipeline(job_id: str, json_path: str, resume_id: int):
    try:
        result = run_pipeline(json_path, resume_id)
        JOB_STORE[job_id] = {
            "status": "done",
            "result": result
        }
    except Exception as e:
        JOB_STORE[job_id] = {
            "status": "failed",
            "error": str(e)
        }


@router.post("/pipeline/analyze")
def analyze(req: PipelineRequest, background_tasks: BackgroundTasks):

    job_id = str(uuid.uuid4())

    JOB_STORE[job_id] = {
        "status": "processing"
    }

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


@router.get("/pipeline/result/{job_id}")
def get_result(job_id: str):

    job = JOB_STORE.get(job_id)

    if not job:
        return {
            "status": "not_found"
        }

    return job