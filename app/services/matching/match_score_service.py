from datetime import datetime
from app.services.normalization.skill_normalizer import normalize_skill

# =========================
# 기술스택 유사어 매핑
# =========================
SKILL_ALIAS = {

    "oracle": {
        "sql": 0.7,
        "rdbms": 0.7
    },

    "mysql": {
        "sql": 0.7,
        "rdbms": 0.7
    },

    "postgresql": {
        "sql": 0.7,
        "rdbms": 0.7
    },

    "nodejs": {
        "javascript": 1.0
    },

    "javascript": {
        "nodejs": 1.0
    },

    "spring": {
        "springboot": 1.0
    },

    "springboot": {
        "spring": 1.0
    }
}

# =========================
# 기술스택 적합도
# =========================
def calculate_tech_stack_fit(
    resume_skills: list,
    job_skills: list
):

    if not job_skills:
        return 0

    resume_set = {

    normalize_skill(skill)

    for skill in resume_skills

    if skill
}

    job_set = {

    normalize_skill(skill)

    for skill in job_skills

    if skill
}

    exact_match = 0
    alias_match = 0

    for resume_skill in resume_set:

        # 완전 일치
        if resume_skill in job_set:

            exact_match += 1
            continue

        # 유사어 일치
        aliases = SKILL_ALIAS.get(
            resume_skill,
            {}
        )

        for alias, weight in aliases.items():

            if alias in job_set:

                alias_match += weight
                break

    print("resume =", resume_set)
    print("job =", job_set)

    print("exact_match =", exact_match)
    print("alias_match =", alias_match)

    score = (

        exact_match
        +
        alias_match

    ) / max(
        len(job_set),
        1
    ) * 100

    return round(min(score, 100), 2)


# =========================
# 경력 적합도
# =========================
def calculate_requirement_fit(
    resume_data: dict,
    job_data: dict
):

    data = resume_data["data"]

    careers = data.get(
        "careers",
        []
    )

    github_repos = data.get(
        "githubRepositories",
        []
    )

    proj_exps = [
        e for e in data.get("experiences", [])
        if e.get("experienceType") == "프로젝트"
    ]

    certificates = data.get(
        "certificates",
        []
    )

    educations = data.get(
        "educations",
        []
    )

    # =====================
    # 경력 점수
    # =====================
    total_months = 0

    for career in careers:

        start = career.get("startYm")
        end = career.get("endYm")

        if not start or not end:
            continue

        try:

            start_dt = datetime.strptime(
                start,
                "%Y-%m"
            )

            end_dt = datetime.strptime(
                end,
                "%Y-%m"
            )

            total_months += (

                (end_dt.year - start_dt.year)
                * 12

                +

                (end_dt.month - start_dt.month)

            )

        except:
            pass

    career_years = total_months / 12

    # =====================
    # 요구 연차
    # =====================
    requirements = str(
        job_data.get(
            "requirements",
            ""
        )
    )

    required_years = 1

    if "7년" in requirements:
        required_years = 7

    elif "5년" in requirements:
        required_years = 5

    elif "3년" in requirements:
        required_years = 3

    career_score = min(
        100,
        (career_years / required_years) * 100
    )

    # =====================
    # 프로젝트 점수 (GitHub 저장소 + 프로젝트 경험 합산)
    # =====================
    project_score = min(
        100,
        (len(github_repos) + len(proj_exps)) * 40
    )

    # =====================
    # 자격증 점수
    # =====================
    certificate_score = min(
        100,
        len(certificates) * 50
    )

    # =====================
    # 학력 점수
    # =====================
    education_score = 100 if educations else 0

    # =====================
    # 최종 계산
    # =====================
    final_score = (

        career_score * 0.4

        +

        project_score * 0.3

        +

        certificate_score * 0.1

        +

        education_score * 0.2

    )
    print("career_score =", career_score)
    print("project_score =", project_score)
    print("certificate_score =", certificate_score)
    print("education_score =", education_score)
    print("requirement_fit =", round(final_score, 2))


    

    return round(
        final_score,
        2
)
# =========================
# 프로젝트 적합도
# =========================
def calculate_action_result_fit(
    analysis_result: dict
):

    projects = analysis_result.get(
        "project_experience",
        []
    )

    text = " ".join(projects).lower()

    score = 20

    keywords = [

        "api",
        "rest",
        "database",
        "db",
        "oracle",
        "mysql",
        "spring",
        "node",
        "upload",
        "auth",
        "jwt",
        "docker",
        "aws"

    ]

    for keyword in keywords:

        if keyword in text:
            score += 8

    return min(score, 100)


# =========================
# 최종 비즈니스 적합도
# =========================
def calculate_business_fit(

    semantic_score,

    tech_score,

    requirement_score,

    action_score,

    culture_score=50

):

    score = (

        semantic_score * 0.50 +

        tech_score * 0.20

        +

        requirement_score * 0.10

        +

        action_score * 0.10

        +

        culture_score * 0.10

    )

    return round(score, 2)


def calculate_culture_fit(
    analysis_result: dict
):

    score = 30

    soft_skills = [

        skill.lower()

        for skill in analysis_result.get(
            "soft_skills",
            []
        )
    ]

    teamwork = str(
        analysis_result.get(
            "teamwork_style",
            ""
        )
    ).lower()

    keywords = {

        "협업": 15,
        "커뮤니케이션": 15,
        "문서화": 10,
        "리더십": 15,
        "책임감": 10,
        "문제 해결": 15

    }

    for keyword, point in keywords.items():

        if keyword in " ".join(soft_skills):

            score += point

    if "협업" in teamwork:
        score += 10

    if "팀" in teamwork:
        score += 5

    return min(score, 100)