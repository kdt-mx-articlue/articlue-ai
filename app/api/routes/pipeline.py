from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.pipeline.service import run_pipeline

router = APIRouter()


# =========================
# REQUEST
# =========================
class PipelineRequest(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]
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