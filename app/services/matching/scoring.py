from app.services.normalization.skill_normalizer import (
    normalize_skill
)


def weighted_score(
    resume,
    job,
    semantic_score=0,
    analysis_result=None
):

    # =========================
    # 기존 이력서 기술스택
    # =========================
    resume_skills = {

        normalize_skill(
            t["tech_name"]
        )

        for t in resume["resume_tech_stack"]
    }

    # =========================
    # LLM 추출 기술 추가
    # =========================
    if analysis_result:

        ai_skills = {

            normalize_skill(skill)

            for skill in analysis_result.get(
                "ai_skills",
                []
            )
        }

        backend_skills = {

            normalize_skill(skill)

            for skill in analysis_result.get(
                "backend_skills",
                []
            )
        }

        technical_skills = {

            normalize_skill(skill)

            for skill in analysis_result.get(
                "technical_skills",
                []
            )
        }

        resume_skills.update(ai_skills)

        resume_skills.update(backend_skills)

        resume_skills.update(technical_skills)

    # =========================
    # 채용공고 기술
    # =========================
    job_skills = {

        normalize_skill(skill)

        for skill in job["required_skills"]
    }

    # =========================
    # 겹치는 기술
    # =========================
    overlap = (
        resume_skills &
        job_skills
    )

    # =========================
    # 기술 점수
    # =========================
    skill_score = (

        len(overlap) /
        len(job_skills)

    ) * 100 if job_skills else 0

    # =========================
    # 경력 점수
    # =========================
    career_years = resume["resume"].get(
        "career_years",
        0
    )

    career_score = min(

        career_years / 3 * 100,

        100
    )

    # =========================
    # 학력 점수
    # =========================
    education_score = (

        80 if resume.get(
            "education"
        )

        else 50
    )

    # =========================
    # 최종 점수
    # =========================
    final_score = (

        skill_score * 0.4 +

        career_score * 0.3 +

        education_score * 0.1 +

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