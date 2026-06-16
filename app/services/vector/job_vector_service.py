from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.analyzers.embedding_service import (
    get_embedding_model
)

print("★★★★★★★★★★★★★★★★")
print(__file__)
print("★★★★★★★★★★★★★★★★")

def save_job_vectors(job_list):
    print("🔥 save_job_vectors 실행")
    print("job 개수 :", len(job_list))

    embeddings = get_embedding_model()

    documents = []

    for job in job_list:

        parsed = job["parsed_result"]

        text = f"""
        회사명: {job['company_name']}

        직무: {job['job_title']}

        기술:
        {' '.join(parsed.get('tech_stacks', []))}

        자격요건:
        {parsed.get('requirements', '')}

        우대사항:
        {parsed.get('preference', '')}

        인재상:
        {parsed.get('team_culture', '')}

        업무:
        {parsed.get('responsibilities', '')}
        """.strip()

        doc = Document(

            page_content=text,

            metadata={

            "job_posting_id":
            job["job_posting_id"],

            "company_name":
            job["company_name"],

            "job_title":
            job["job_title"]
            }
            )

        documents.append(doc)

    vector_store = Chroma.from_documents(

    documents=documents,

    embedding=embeddings,

    ids=[
        str(job["job_posting_id"])
        for job in job_list
    ],

    persist_directory=(
        "app/data/vectors/job_vectors"
    )
    
)
    print("✅ Job Vector 저장 완료")

    return vector_store