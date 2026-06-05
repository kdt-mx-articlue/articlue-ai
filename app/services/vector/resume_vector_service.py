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


def save_resume_vector(resume_data, analysis_result,star_analysis=None):

    embeddings = get_embedding_model()

    # =========================
    # 안전한 구조 처리
    # =========================
    resume = resume_data.get("resume", resume_data)

    tech_stack = [
        tech.get("tech_name", "")
        for tech in resume_data.get("resume_tech_stack", [])
    ]

    technical_skills = analysis_result.get("technical_skills", [])
    ai_skills = analysis_result.get("ai_skills", [])
    backend_skills = analysis_result.get("backend_skills", [])
    personality_traits = analysis_result.get("personality_traits", [])

    # =========================
    # vector text 생성
    # =========================
    vector_text = f"""
이름: {resume.get("name", "")}
희망직무: {analysis_result.get("career_orientation", "")}
희망지역: {resume.get("desired_location", "")}
경력연차: {resume.get("career_years", 0)}

기술스택: {' '.join(tech_stack)}

기술역량: {' '.join(technical_skills)}

AI 기술: {' '.join(ai_skills)}

백엔드 기술: {' '.join(backend_skills)}

소프트스킬: {' '.join(analysis_result.get("soft_skills", []))}

성향: {' '.join(personality_traits)}

프로젝트 경험: {' '.join(analysis_result.get("project_experience", []))}
""".strip()

    document = Document(
        page_content=vector_text,
        metadata={
            "resume_id": resume.get("resume_id"),
            "name": resume.get("name"),
            "desired_location": resume.get("desired_location"),
            "career_years": resume.get("career_years", 0),
        }
    )

    # =========================
    # vector DB 저장
    # =========================
    vector_store = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    vector_store.add_documents([document])

    # =========================
    # JSON 저장도 같이
    # =========================
    os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)

    output_file = os.path.join(
        OUTPUT_JSON_DIR,
        f"resume_vector_{resume.get('resume_id', 'unknown')}.json"
    )

    print("🔥 저장직전")
    print(analysis_result)

    json_dump = {
        "vector_text": vector_text,
        "metadata": document.metadata,
        "analysis_result": analysis_result,
        "star_analysis": star_analysis,
        "resume_data": resume_data,
        "saved_at": datetime.now().isoformat()
}

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(json_dump, f, ensure_ascii=False, indent=2)

    return vector_store