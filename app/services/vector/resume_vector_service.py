import json
import os
from datetime import datetime

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.services.embedding_service import get_embedding_model


PERSIST_DIR = os.path.abspath(
    os.path.join("app", "data", "vectors", "resume_vectors")
)

OUTPUT_JSON_DIR = os.path.abspath(
    os.path.join("app", "data", "outputs")
)


# =========================
# 안전 metadata 변환
# =========================
def flatten_metadata(data: dict):

    flat = {}

    for k, v in data.items():

        if isinstance(v, (str, int, float, bool)) or v is None:
            flat[k] = v

        elif isinstance(v, list):
            flat[k] = ",".join(map(str, v))

        elif isinstance(v, dict):
            flat[k] = str(v)

        else:
            flat[k] = str(v)

    return flat


def save_resume_vector(
    resume_data,
    analysis_result,
    star_analysis=None,
    github_traits=None,
    github_profile=None
):

    github_profile = github_profile or {}

    embeddings = get_embedding_model()

    # =========================
    # 데이터 추출
    # =========================
    tech_stack = [
        tech.get("techName", "")
        for tech in resume_data.get("techStacks", [])
    ]

    technical_skills = analysis_result.get("technical_skills", [])
    ai_skills = analysis_result.get("ai_skills", [])
    backend_skills = analysis_result.get("backend_skills", [])
    personality_traits = analysis_result.get("personality_traits", [])

    desired_locations = [
        loc.get("locationName", "")
        for loc in resume_data.get("desiredLocations", [])
    ]

    # =========================
    # vector text
    # =========================
    vector_text = f"""
희망직무:
{resume_data.get("desiredJob", "")}

자기소개:
{resume_data.get("introduction", "")}

희망지역:
{' '.join(desired_locations)}

기술스택:
{' '.join(tech_stack)}

기술역량:
{' '.join(technical_skills)}

AI 기술:
{' '.join(ai_skills)}

백엔드 기술:
{' '.join(backend_skills)}

소프트스킬:
{' '.join(analysis_result.get("soft_skills", []))}

성향:
{' '.join(personality_traits)}

프로젝트 경험:
{' '.join(analysis_result.get("project_experience", []))}

GitHub 개발성향:
{' '.join(github_traits or [])}

GitHub 활동성:
{github_profile.get("activity_score", 0)}
""".strip()

    # =========================
    # metadata (핵심 수정)
    # =========================
    raw_metadata = {
        "resume_id": resume_data.get("resumeId"),
        "member_id": resume_data.get("memberId"),
        "resume_title": resume_data.get("resumeTitle"),
        "desired_job": resume_data.get("desiredJob"),

        "desired_locations": desired_locations,

        "technical_skills": technical_skills,
        "ai_skills": ai_skills,
        "backend_skills": backend_skills,
        "soft_skills": analysis_result.get("soft_skills", []),
        "personality_traits": personality_traits,

        "career_score": analysis_result.get("career_score", 0),
        "skill_score": analysis_result.get("skill_score", 0),
    }

    metadata = flatten_metadata(raw_metadata)

    # =========================
    # Document 생성 (정상)
    # =========================
    document = Document(
        page_content=vector_text,
        metadata=metadata
    )

    # =========================
    # Vector DB
    # =========================
    vector_store = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    vector_store.add_documents(
        documents=[document],
        ids=[str(resume_data.get("resumeId"))]
    )

    # =========================
    # JSON 저장
    # =========================
    os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)

    output_file = os.path.join(
        OUTPUT_JSON_DIR,
        f"resume_vector_{resume_data.get('resumeId')}.json"
    )

    json_dump = {
        "vector_text": vector_text,
        "metadata": metadata,
        "analysis_result": analysis_result,
        "star_analysis": star_analysis,
        "github_traits": github_traits,
        "github_profile": github_profile,
        "resume_data": resume_data,
        "saved_at": datetime.now().isoformat()
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_dump, f, ensure_ascii=False, indent=2)

    return vector_store