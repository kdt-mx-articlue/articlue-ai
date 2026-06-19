from fastapi import APIRouter

from app.api.schemas.interview.final_match_schema import (
    FinalMatchRequest
)

from app.services.interview.final_match_service import (
    build_final_match
)

router = APIRouter()


@router.post("/final-match")
def final_match(
    request: FinalMatchRequest
):

    result = build_final_match(

        request.resume,

        request.interview

    )

    return {

    "resume_id":
    request.resume_id,

    "job_posting_id":
    request.job_posting_id,

    "company_name":
    request.company_name,

    "analysis": {

        "type":
        "FINAL",

        "overall_score":
        result["overall_score"],

        "metrics":
        result["metrics"]

    }

}