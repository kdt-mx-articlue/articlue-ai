from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.pipeline.service import run_pipeline, run_single_job_pipeline

router = APIRouter()


# =========================
# REQUEST
# =========================
class PipelineRequest(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]
    analysis_stage: str = "RESUME"


class SingleJobRequest(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]
    job_posting_id: int
    analysis_stage: str = "RESUME"


# =========================
# ANALYZE
# =========================
@router.post("/pipeline/analyze")
def analyze(req: PipelineRequest):

    try:

        print("========== Request ==========")
        print(req.model_dump())
        print("=============================")

        resume_data = req.model_dump()

        resume_id = (
            resume_data["data"]
            .get("resumeId")
        )

        if not resume_id:

            raise HTTPException(
                status_code=400,
                detail="resumeId 없음"
            )

        analysis_stage = resume_data.get("analysis_stage", "RESUME").upper()

        result = run_pipeline(
            resume_data=resume_data,
            resume_id=resume_id,
            analysis_stage=analysis_stage
        )

        return {
            "success": True,
            "message": "분석 완료",
            "result": result
        }

    except Exception as e:

        import traceback

        print("❌ PIPELINE ERROR")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# =========================
# SINGLE JOB ANALYZE
# =========================
@router.post("/pipeline/analyze-single")
def analyze_single(req: SingleJobRequest):
    """
    단일 공고에 대해서만 GPT 정밀 분석 수행.
    전체 484개 파이프라인 없이 GPT 1회만 호출 → 빠름.
    """

    try:

        resume_data = req.model_dump()

        resume_id = resume_data["data"].get("resumeId")

        if not resume_id:
            raise HTTPException(status_code=400, detail="resumeId 없음")

        result = run_single_job_pipeline(
            resume_data=resume_data,
            resume_id=resume_id,
            job_posting_id=req.job_posting_id
        )

        return {
            "success": True,
            "message": "단일 기업 분석 완료",
            "result": result
        }

    except Exception as e:

        import traceback

        print("❌ SINGLE JOB ANALYSIS ERROR")
        print(traceback.format_exc())

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )