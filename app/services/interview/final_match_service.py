from app.services.interview.interview_score_service import (
    apply_interview_scores,
    calculate_final_overall_score
)

def build_final_match(
    resume_data,
    interview_data
):

    final_metrics = apply_interview_scores(
        resume_data["metrics"],
        interview_data
    )

    overall_score = calculate_final_overall_score(
        final_metrics
    )

    return {
        "overall_score": overall_score,
        "metrics": final_metrics
    }