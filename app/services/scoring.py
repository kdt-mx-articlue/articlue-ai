def weighted_score(resume, job):

    resume_skills = {t["tech_name"] for t in resume["resume_tech_stack"]}
    job_skills = set(job["required_skills"])

    overlap = resume_skills & job_skills

    skill_score = (len(overlap) / len(job_skills)) * 100 if job_skills else 0

    career_years = resume["resume"].get("career_years", 0)
    career_score = min(career_years / 3 * 100, 100)

    education_score = 80 if resume.get("education") else 50

    final_score = (
        skill_score * 0.5 +
        career_score * 0.3 +
        education_score * 0.2
    )

    return {
        "skill_score": round(skill_score, 2),
        "career_score": round(career_score, 2),
        "education_score": education_score,
        "final_score": round(final_score, 2),
        "matched_skills": list(overlap)
    }