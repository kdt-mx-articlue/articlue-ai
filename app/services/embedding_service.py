from langchain_community.embeddings import HuggingFaceEmbeddings


def get_embedding_model():
    """
    Chroma + Matching에서 동일하게 사용할 embedding 모델
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )