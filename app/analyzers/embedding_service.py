from langchain_openai import OpenAIEmbeddings


def get_embedding_model():

    """
    OpenAI Embedding 모델 생성
    """

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    return embeddings