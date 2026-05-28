from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.analyzers.embedding_service import get_embedding_model


def save_to_vector_db(
    semantic_text: str,
    analysis_result: str,
    resume_id: int
):

    embeddings = get_embedding_model()

    document = Document(
        page_content=semantic_text,
        metadata={
            "resume_id": resume_id,
            "analysis_result": analysis_result
        }
    )

    # ✅ DB 연결 (재사용 구조)
    vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory="app/data/embeddings"
    )

    # ✅ 저장
    vector_store.add_documents([document])

    # (선택) 강제 저장
    vector_store.persist()

    return vector_store