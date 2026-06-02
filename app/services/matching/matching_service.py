from langchain_community.embeddings import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


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
# Job Text
# =========================
def build_job_text(job):

    parsed = job.get(
        "parsed_result",
        {}
    )

    return f"""
직무: {parsed.get("role", "")}

기술: {safe_join(parsed.get("required_skills", []))}

우대기술: {safe_join(parsed.get("preferred_skills", []))}

소프트스킬: {safe_join(parsed.get("soft_skills", []))}

업무: {safe_join(parsed.get("responsibilities", []))}
""".strip()


# =========================
# Candidate Text
# =========================
def build_candidate_text(candidate):

    parsed = candidate.get(
        "analysis_result",
        {}
    )

    return f"""
성향: {safe_join(parsed.get("personality_traits", []))}

기술: {safe_join(parsed.get("technical_skills", []))}

소프트스킬: {safe_join(parsed.get("soft_skills", []))}

문제해결: {parsed.get("problem_solving", "") or ""}

희망직무: {parsed.get("job_preference", "") or ""}
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
# 전체 공고 매칭
# =========================
def match_candidate_to_jobs(
    candidate_data,
    jobs_data
):

    candidate_text = build_candidate_text(
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