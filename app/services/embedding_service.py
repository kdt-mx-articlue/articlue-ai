import json

from sentence_transformers import (
    SentenceTransformer
)

from sklearn.metrics.pairwise import (
    cosine_similarity
)


# 모델 로드
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


def build_job_text(job_data):

    parsed = job_data.get(
        "parsed_result",
        {}
    )

    return f"""
    직무:
    {parsed.get("role", "")}

    기술:
    {' '.join(parsed.get("required_skills", []))}

    우대기술:
    {' '.join(parsed.get("preferred_skills", []))}

    소프트스킬:
    {' '.join(parsed.get("soft_skills", []))}

    업무:
    {' '.join(parsed.get("responsibilities", []))}
    """


def build_candidate_text(candidate_data):

    parsed = candidate_data.get(
        "parsed_result",
        {}
    )

    return f"""
    성향:
    {' '.join(parsed.get("personality_traits", []))}

    기술:
    {' '.join(parsed.get("technical_skills", []))}

    소프트스킬:
    {' '.join(parsed.get("soft_skills", []))}

    문제해결:
    {parsed.get("problem_solving", "")}

    희망직무:
    {parsed.get("job_preference", "")}
    """


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

    candidate_embedding = model.encode(
        [candidate_text]
    )

    job_embedding = model.encode(
        [job_text]
    )

    score = cosine_similarity(
        candidate_embedding,
        job_embedding
    )[0][0]

    return round(
        float(score),
        4
    )