import json

from app.services.embedding_service import (
    calculate_matching_score
)


def extract_skill_matches(
    candidate_data,
    job_data
):

    """
    공통 기술 / 부족 기술 추출
    """

    candidate_skills = set(
        candidate_data
        .get(
            "parsed_result",
            {}
        )
        .get(
            "technical_skills",
            []
        )
    )

    job_skills = set(
        job_data
        .get(
            "parsed_result",
            {}
        )
        .get(
            "required_skills",
            []
        )
    )

    matched_skills = list(
        candidate_skills & job_skills
    )

    missing_skills = list(
        job_skills - candidate_skills
    )

    return (
        matched_skills,
        missing_skills,
        job_skills
    )


def calculate_skill_score(
    matched_skills,
    job_skills
):

    """
    기술 매칭 점수 계산
    """

    if len(job_skills) == 0:

        return 0

    return len(
        matched_skills
    ) / len(
        job_skills
    )


def generate_match_reasons(
    final_score,
    matched_skills,
    missing_skills
):

    """
    추천 이유 생성
    """

    reasons = []

    # 최종 점수 기준
    if final_score >= 0.8:

        reasons.append(
            "직무 적합도가 매우 높음"
        )

    elif final_score >= 0.6:

        reasons.append(
            "직무 적합도가 높음"
        )

    else:

        reasons.append(
            "일부 역량만 일치"
        )

    # 공통 기술
    if matched_skills:

        reasons.append(
            f"보유 기술 일치: {', '.join(matched_skills)}"
        )

    # 부족 기술
    if missing_skills:

        reasons.append(
            f"추가 필요 기술: {', '.join(missing_skills)}"
        )

    return reasons


def match_candidate_to_jobs():

    """
    구직자 ↔ 채용공고 매칭
    """

    # 구직자 로드
    with open(
        "app/data/outputs/parsed_candidate.json",
        "r",
        encoding="utf-8"
    ) as f:

        candidate_data = json.load(f)

    # 채용공고 로드
    with open(
        "app/data/outputs/parsed_jobs.json",
        "r",
        encoding="utf-8"
    ) as f:

        jobs_data = json.load(f)

    results = []

    for job in jobs_data:

        # semantic similarity
        semantic_score = (
            calculate_matching_score(
                candidate_data,
                job
            )
        )

        # 기술 매칭 분석
        (
            matched_skills,
            missing_skills,
            job_skills
        ) = extract_skill_matches(
            candidate_data,
            job
        )

        # 기술 점수
        skill_score = (
            calculate_skill_score(
                matched_skills,
                job_skills
            )
        )

        # 최종 점수 계산
        final_score = round(
            (
                semantic_score * 0.7
                +
                skill_score * 0.3
            ),
            4
        )

        # 추천 이유 생성
        match_reasons = generate_match_reasons(
            final_score,
            matched_skills,
            missing_skills
        )

        # 결과 저장
        results.append({

            "candidate_name":
            candidate_data.get(
                "name"
            ),

            "job_title":
            job.get(
                "job_title"
            ),

            "company_name":
            job.get(
                "company_name"
            ),

            "semantic_score":
            round(
                semantic_score,
                4
            ),

            "skill_score":
            round(
                skill_score,
                4
            ),

            "matching_score":
            final_score,

            "matched_skills":
            matched_skills,

            "missing_skills":
            missing_skills,

            "match_reasons":
            match_reasons
        })

    # 점수순 정렬
    results.sort(
        key=lambda x:
        x["matching_score"],
        reverse=True
    )

    return results