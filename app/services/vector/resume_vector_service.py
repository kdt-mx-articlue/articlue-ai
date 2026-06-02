from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.services.embedding_service import get_embedding_model
import os

PERSIST_DIR = os.path.abspath(
    os.path.join("app", "data", "vectors", "resume_vectors")
)


def save_resume_vector(resume_data, analysis_result):

    embeddings = get_embedding_model()

    tech_stack = [
        tech.get("tech_name", "")
        for tech in resume_data.get("resume_tech_stack", [])
    ]

    technical_skills = analysis_result.get("technical_skills", [])
    personality_traits = analysis_result.get("personality_traits", [])
    soft_skills = analysis_result.get("soft_skills", [])

    vector_text = f"""
이름: {resume_data["resume"].get("name", "")}
희망직무: {analysis_result.get("job_preference", "")}
기술스택: {' '.join(tech_stack)}
기술역량: {' '.join(technical_skills)}
소프트스킬: {' '.join(soft_skills)}
성향: {' '.join(personality_traits)}
""".strip()

    document = Document(
        page_content=vector_text,
        metadata={
            "resume_id": resume_data["resume"].get("resume_id"),
            "name": resume_data["resume"].get("name"),
            "desired_location": resume_data["resume"].get("desired_location"),
        }
    )

    vector_store = Chroma(
        persist_directory=PERSIST_DIR,
        embedding_function=embeddings
    )

    vector_store.add_documents([document])

    return vector_store