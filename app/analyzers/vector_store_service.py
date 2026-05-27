from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.analyzers.embedding_service import get_embedding_model


def save_to_vector_db(
    semantic_text: str,
    analysis_result: str,
    resume_id: int
):

    """
    ChromaDB 저장
    """

    embeddings = get_embedding_model()

    document = Document(
        page_content=semantic_text,
        metadata={
            "resume_id": resume_id,
            "analysis_result": analysis_result
        }
    )

    vector_store = Chroma.from_documents(
        documents=[document],
        embedding=embeddings,
        persist_directory="app/data/embeddings"
    )

    return vector_store