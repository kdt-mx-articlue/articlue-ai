from app.services.normalization.skill_normalizer import normalize_skill
from datetime import datetime


def calc_career_years(careers):

    total_months = 0

    for c in careers:

        start = c.get("startYm")
        end = c.get("endYm")

        if not start:
            continue

        try:

            sy, sm = map(int, start.split("-"))

            if end:
                ey, em = map(int, end.split("-"))
            else:
                now = datetime.now()
                ey, em = now.year, now.month

            total_months += (
                (ey - sy) * 12
                +
                (em - sm)
            )

        except:
            continue

    return total_months / 12


def weighted_score(
    resume,
    job,
    semantic_score=0,
    analysis_result=None
):

    # =========================
    # resume 실제 데이터
    # =========================
    data = resume.get(
        "data",
        {}
    )

    # =========================
    # 기술스택
    # =========================
    resume_skills = {

        normalize_skill(
            t.get(
                "techName",
                ""
            )
        )

        for t in data.get(
            "techStacks",
            []
        )

        if t.get("techName")
    }

    # =========================
    # LLM 추출 스킬 추가
    # =========================
    if analysis_result:

        ai_skills = {

            normalize_skill(s)

            for s in analysis_result.get(
                "ai_skills",
                []
            )

        }

        backend_skills = {

            normalize_skill(s)

            for s in analysis_result.get(
                "backend_skills",
                []
            )

        }

        technical_skills = {

            normalize_skill(s)

            for s in analysis_result.get(
                "technical_skills",
                []
            )

        }

        resume_skills.update(ai_skills)
        resume_skills.update(backend_skills)
        resume_skills.update(technical_skills)

    # =========================
    # 채용공고 스킬
    # =========================
    job_skills = {

        normalize_skill(s)

        for s in job.get(
            "required_skills",
            []
        )

    }

    overlap = (
        resume_skills
        &
        job_skills
    )

    skill_score = (

        len(overlap)
        /
        len(job_skills)

    ) * 100 if job_skills else 0

    # =========================
    # 경력
    # =========================
    career_years = calc_career_years(

        data.get(
            "careers",
            []
        )

    )

    career_score = min(
        (
            career_years
            /
            3
        ) * 100,
        100
    )

    # =========================
    # 학력
    # =========================
    education_score = (

        80

        if data.get(
            "educations"
        )

        else 50

    )

    # =========================
    # 디버깅
    # =========================
    print(
        "resume_skills =",
        resume_skills
    )

    print(
        "job_skills =",
        job_skills
    )

    print(
        "overlap =",
        overlap
    )

    print(
        "career_years =",
        career_years
    )

    # =========================
    # 최종 점수
    # =========================
    final_score = (

        skill_score * 0.4

        +

        career_score * 0.3

        +

        education_score * 0.1

        +

        semantic_score * 0.2

    )

    return {

        "skill_score": round(
            skill_score,
            2
        ),

        "career_score": round(
            career_score,
            2
        ),

        "education_score": education_score,

        "semantic_score": round(
            semantic_score,
            2
        ),

        "final_score": round(
            final_score,
            2
        ),

        "matched_skills": list(
            overlap
        )

    }