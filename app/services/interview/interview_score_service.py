def apply_interview_scores(
    metrics,
    interview
):
    """
    1차 이력서 점수 +
    2차 면접 점수 반영
    """

    logic_score = interview.get(
        "logic_score",
        0
    )

    tech_understanding_score = interview.get(
        "tech_understanding_score",
        0
    )

    business_link_score = interview.get(
        "business_link_score",
        0
    )

    evidence_score = interview.get(
        "evidence_score",
        0
    )

    job_fit_score = interview.get(
        "job_fit_score",
        0
    )

    # =========================
    # 점수 재계산
    # =========================

    metrics["business_fit"]["score"] = round(

        metrics["business_fit"]["score"] * 0.6

        +

        business_link_score * 0.2

        +

        job_fit_score * 0.2,

        2
    )

    metrics["tech_stack_fit"]["score"] = round(

        metrics["tech_stack_fit"]["score"] * 0.7

        +

        tech_understanding_score * 0.3,

        2
    )

    metrics["action_result_fit"]["score"] = round(

        metrics["action_result_fit"]["score"] * 0.7

        +

        evidence_score * 0.3,

        2
    )

    metrics["requirement_fit"]["score"] = round(

        metrics["requirement_fit"]["score"] * 0.7

        +

        logic_score * 0.3,

        2
    )

    metrics["culture_fit"]["score"] = round(

        metrics["culture_fit"]["score"] * 0.5

        +

        logic_score * 0.2

        +

        evidence_score * 0.3,

        2
    )

    # =========================
    # 이유 보강
    # =========================

    metrics["business_fit"]["reason_text"] += (

        f" 면접 결과 직무적합도({job_fit_score})와 "
        f"비즈니스 이해도({business_link_score})가 추가 반영되었습니다."

    )

    metrics["tech_stack_fit"]["reason_text"] += (

        f" 기술 이해도 평가({tech_understanding_score})가 반영되었습니다."

    )

    metrics["action_result_fit"]["reason_text"] += (

        f" 경험 근거 제시 능력({evidence_score})이 반영되었습니다."

    )

    metrics["requirement_fit"]["reason_text"] += (

        f" 논리적 사고 평가({logic_score})가 반영되었습니다."

    )

    metrics["culture_fit"]["reason_text"] += (

        " 면접 과정에서의 커뮤니케이션 및 협업 역량이 반영되었습니다."

    )

    return metrics


# =====================================
# 최종 종합 점수
# =====================================
def calculate_final_overall_score(
    metrics
):
    """
    최종 기업 추천 점수

    business_fit      30%
    tech_stack_fit    25%
    requirement_fit   20%
    action_result_fit 15%
    culture_fit       10%
    """

    overall_score = (

        metrics["business_fit"]["score"] * 0.30

        +

        metrics["tech_stack_fit"]["score"] * 0.25

        +

        metrics["requirement_fit"]["score"] * 0.20

        +

        metrics["action_result_fit"]["score"] * 0.15

        +

        metrics["culture_fit"]["score"] * 0.10

    )

    return round(
        overall_score,
        2
    )