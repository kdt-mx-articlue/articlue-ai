from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.analyzers.embedding_service import (
    get_embedding_model
)

print("★★★★★★★★★★★★★★★★")
print(__file__)
print("★★★★★★★★★★★★★★★★")

JOB_VECTOR_DIR = "app/data/vectors/job_vectors"


def build_job_document(job):

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

    return Document(

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


def get_job_vector_store():

    return Chroma(
        embedding_function=get_embedding_model(),
        persist_directory=JOB_VECTOR_DIR
    )


def save_job_vectors(job_list):
    print("🔥 save_job_vectors 실행")
    print("job 개수 :", len(job_list))

    embeddings = get_embedding_model()

    documents = [build_job_document(job) for job in job_list]

    vector_store = Chroma.from_documents(

    documents=documents,

    embedding=embeddings,

    ids=[
        str(job["job_posting_id"])
        for job in job_list
    ],

    persist_directory=(
        JOB_VECTOR_DIR
    )
    
)
    print("✅ Job Vector 저장 완료")

    return vector_store


def upsert_job_vectors(job_list):
    """
    수집 공고 벡터 추가/갱신 — 같은 ID 는 삭제 후 다시 추가 (전체 재생성 없음)
    """
    if not job_list:
        return

    vector_store = get_job_vector_store()
    ids = [str(job["job_posting_id"]) for job in job_list]

    vector_store.delete(ids=ids)
    vector_store.add_documents(
        [build_job_document(job) for job in job_list],
        ids=ids
    )


def remove_job_vectors(job_ids):
    """
    마감 공고 벡터 제거
    """
    if not job_ids:
        return

    get_job_vector_store().delete(ids=[str(job_id) for job_id in job_ids])
