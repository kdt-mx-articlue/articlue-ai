from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.analyzers.embedding_service import (
    get_embedding_model
)


def save_job_vectors(job_list):

    embeddings = get_embedding_model()

    documents = []

    for job in job_list:

        parsed = job["parsed_result"]

        text = f"""
        회사명: {job['company_name']}

        직무: {job['job_title']}

        기술:
        {' '.join(parsed.get('required_skills', []))}

        우대:
        {' '.join(parsed.get('preferred_skills', []))}

        """

        doc = Document(

            page_content=text,

            metadata={

                "job_id": job["job_id"],

                "company_name": (
                    job["company_name"]
                ),

                "job_title": (
                    job["job_title"]
                )
            }
        )

        documents.append(doc)

    vector_store = Chroma.from_documents(

        documents=documents,

        embedding=embeddings,

        persist_directory=(
            "app/data/vectors/job_vectors"
        )
    )

    return vector_store