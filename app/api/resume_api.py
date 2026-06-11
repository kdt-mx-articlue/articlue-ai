from fastapi import APIRouter
from pydantic import BaseModel

from app.services.candidate.candidate_json_service import (
    process_candidate_json_data
)

router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


class ResumeRequest(BaseModel):
    resume: dict


@router.post("/analyze")
def analyze_resume(request: ResumeRequest):

    result = process_candidate_json_data(
        request.resume
    )

    return {
        "success": True,
        "result": result
    }