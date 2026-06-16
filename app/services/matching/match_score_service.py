from datetime import datetime


# =========================
# 기술스택 유사어 매핑
# =========================
SKILL_ALIAS = {

    "spring boot": [
        "spring"
    ],

    "spring": [
        "spring boot"
    ],

    "oracle": [
        "sql",
        "rdbms"
    ],

    "mysql": [
        "sql",
        "rdbms"
    ],

    "postgresql": [
        "sql",
        "rdbms"
    ],

    "node.js": [
        "javascript"
    ],

    "express.js": [
        "node.js",
        "javascript"
    ]

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
        str(skill).lower().strip()
        for skill in resume_skills
    }

    job_set = {
        str(skill).lower().strip()
        for skill in job_skills
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
            []
        )

        for alias in aliases:

            if alias in job_set:

                alias_match += 0.5
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

    return round(score, 2)


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

    projects = data.get(
        "githubRepositories",
        []
    )

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
    # 프로젝트 점수
    # =====================
    project_score = min(
        100,
        len(projects) * 40
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