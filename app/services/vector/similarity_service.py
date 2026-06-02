from langchain_chroma import Chroma

from app.analyzers.embedding_service import (
    get_embedding_model
)


def search_similar_jobs(
    query_text,
    k=5
):

    embeddings = get_embedding_model()

    db = Chroma(

        persist_directory=
        "app/data/job_vectors",

        embedding_function=
        embeddings
    )

    docs = db.similarity_search_with_score(

        query_text,

        k=k
    )

    results = []

    for doc, score in docs:

        results.append({

            "score": score,

            "metadata": doc.metadata,

            "content": doc.page_content
        })

    return results