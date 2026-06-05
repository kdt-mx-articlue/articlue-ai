from langchain_community.embeddings import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from app.services.matching.skill_chipset import (
    expand_skills
)



# =========================
# Embedding Model
# =========================
model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# =========================
# 공통 유틸
# =========================
def safe_join(values):

    if not values:
        return ""

    return " ".join(
        [
            str(v).strip()
            for v in values
            if v and str(v).strip()
        ]
    )

    # =========================
# 기술 스택 확장
# =========================
TECH_RELATIONS = {

    "Python": [
        "FastAPI",
        "Django",
        "Flask",
        "Pandas",
        "NumPy"
    ],

    "FastAPI": [
        "Python",
        "REST API",
        "Swagger"
    ],

    "Spring": [
        "Java",
        "Spring Boot",
        "JPA"
    ],

    "MySQL": [
        "SQL",
        "Database"
    ],

    "LangChain": [
        "LLM",
        "RAG",
        "Prompt Engineering"
    ],

    "ChromaDB": [
        "Vector DB",
        "Embedding",
        "RAG"
    ]
}


def expand_skills(skills):

    expanded = set(skills)

    for skill in skills:

        related = TECH_RELATIONS.get(
            skill,
            []
        )

        expanded.update(related)

    return list(expanded)


# =========================
# Job Text
# =========================
def build_job_text(job):

    parsed = job.get(
        "parsed_result",
        {}
    )
    job_skills = expand_skills(
    parsed.get(
        "tech_stacks",
        []
    )
)

    return f"""
직무: {job.get("job_title", "")}

경력조건: {parsed.get("career_level", "")}

기술스택:
{safe_join(job_skills)}

자격요건:
{parsed.get("requirements", "")}

우대사항:
{parsed.get("preference", "")}

인재상:
{parsed.get("team_culture", "")}

주요업무:
{parsed.get("responsibilities", "")}

복지혜택:
{parsed.get("benefits", "")}
""".strip()


# =========================
# Candidate Text
# =========================
def build_candidate_text(candidate):

    parsed = candidate.get(
        "analysis_result",
        {}
    )

    resume_data = candidate.get(
        "resume_data",
        {}
    )

    resume_skills = [
        tech.get("tech_name", "")
        for tech in resume_data.get(
            "resume_tech_stack",
            []
        )
    ]

    resume_skills = expand_skills(
    resume_skills
)

    career_years = (
        resume_data
        .get("resume", {})
        .get("career_years", 0)
    )

    return f"""
희망직무:
{parsed.get("career_orientation", "")}

총 경력:
{career_years}년

보유기술스택:
{safe_join(resume_skills)}

기술역량:
{safe_join(parsed.get("technical_skills", []))}

AI기술:
{safe_join(parsed.get("ai_skills", []))}

백엔드기술:
{safe_join(parsed.get("backend_skills", []))}

소프트스킬:
{safe_join(parsed.get("soft_skills", []))}

성향:
{safe_join(parsed.get("personality_traits", []))}

문제해결:
{parsed.get("problem_solving", "")}

프로젝트경험:
{safe_join(parsed.get("project_experience", []))}
""".strip()

# =========================
# Requirement Fit Job Text
# =========================
def build_requirement_text(job):

    parsed = job.get(
        "parsed_result",
        {}
    )

    return f"""
자격요건:
{parsed.get("requirements", "")}

주요업무:
{parsed.get("responsibilities", "")}
""".strip()


# =========================
# Requirement Fit Resume Text
# =========================
def build_resume_requirement_text(candidate):

    parsed = candidate.get(
        "analysis_result",
        {}
    )

    resume_data = candidate.get(
        "resume_data",
        {}
    )

    career_text = ""

    for career in resume_data.get(
        "career",
        []
    ):

        career_text += f"""
회사:
{career.get("company_name", "")}

부서:
{career.get("department", "")}

직무:
{career.get("position", "")}

주요성과:
{career.get("main_achievement", "")}
"""

    return f"""
기술역량:
{safe_join(parsed.get("technical_skills", []))}

프로젝트경험:
{safe_join(parsed.get("project_experience", []))}

문제해결:
{parsed.get("problem_solving", "")}

경력:
{career_text}
""".strip()


# =========================
# Embedding
# =========================
def get_embeddings(
    candidate_text,
    job_texts
):

    all_texts = [candidate_text] + job_texts

    embeddings = model.embed_documents(
        all_texts
    )

    return (
        embeddings[0],
        embeddings[1:]
    )


# =========================
# Similarity Score
# =========================
def score(
    candidate_embedding,
    job_embedding
):

    return round(
        float(
            cosine_similarity(
                [np.array(candidate_embedding)],
                [np.array(job_embedding)]
            )[0][0]
        ),
        4
    )


# =========================
# 단일 공고 매칭
# =========================
def calculate_matching_score(
    candidate_data,
    job_data
):

    candidate_text = build_candidate_text(
        candidate_data
    )

    job_text = build_job_text(
        job_data
    )

    candidate_embedding, job_embeddings = (
        get_embeddings(
            candidate_text,
            [job_text]
        )
    )

    return score(
        candidate_embedding,
        job_embeddings[0]
    )

# =========================
# Requirement Fit
# =========================
def calculate_requirement_fit(
    candidate_data,
    job_data
):

    candidate_text = build_candidate_text(
        candidate_data
    )

    parsed = job_data.get(
        "parsed_result",
        {}
    )

    # =========================
    # 필수요건
    # =========================
    requirement_text = f"""
    {parsed.get("requirements","")}
    {safe_join(parsed.get("tech_stacks", []))}
    """

    # =========================
    # 주요업무
    # =========================
    responsibility_text = f"""
    {parsed.get("responsibilities","")}
    """

    # =========================
    # 우대사항
    # =========================
    preference_text = f"""
    {parsed.get("preference","")}
    """

    candidate_embedding = model.embed_query(
        candidate_text
    )

    requirement_embedding = model.embed_query(
        requirement_text
    )

    responsibility_embedding = model.embed_query(
        responsibility_text
    )

    preference_embedding = model.embed_query(
        preference_text
    )

    requirement_score = score(
        candidate_embedding,
        requirement_embedding
    )

    responsibility_score = score(
        candidate_embedding,
        responsibility_embedding
    )

    preference_score = score(
        candidate_embedding,
        preference_embedding
    )

    final_score = (
    requirement_score * 0.7
    +
    responsibility_score * 0.25
    +
    preference_score * 0.05
)

    return round(
        final_score,
        4
    )

# =========================
# 전체 공고 매칭
# =========================
def match_candidate_to_jobs(
    candidate_data,
    jobs_data
):

    candidate_text = build_resume_requirement_text(
        candidate_data
    )

    job_texts = [
        build_job_text(job)
        for job in jobs_data
    ]

    candidate_embedding, job_embeddings = (
        get_embeddings(
            candidate_text,
            job_texts
        )
    )

    results = []

    for job, job_embedding in zip(
        jobs_data,
        job_embeddings
    ):

        results.append({

            "job_id":
            job.get(
                "job_id",
                -1
            ),

            "company_name":
            job.get(
                "company_name",
                ""
            ),

            "job_title":
            job.get(
                "job_title",
                ""
            ),

            "matching_score":
            score(
                candidate_embedding,
                job_embedding
            ),

            "parsed_result":
            job.get(
                "parsed_result",
                {}
            )
        })

    results.sort(
        key=lambda x: x[
            "matching_score"
        ],
        reverse=True
    )

    return results