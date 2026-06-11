from fastapi import APIRouter

from app.services.candidate.candidate_json_service import (
    process_candidate_data
)

router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


@router.post("/analyze")
async def analyze_resume(
    resume: dict
):

    result = process_candidate_data(
        resume
    )

    return result