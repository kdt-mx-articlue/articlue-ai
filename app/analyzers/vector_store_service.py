from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.analyzers.embedding_service import get_embedding_model
import json




def get_resume_by_id(resume_id: int):

    vector_store = get_vector_store()

    result = vector_store.get(
        ids=[str(resume_id)]
    )

    return result
# =========================
# metadata 안전 변환기
# =========================
def safe_metadata(data: dict):

    safe = {}

    for k, v in data.items():

        if v is None:
            safe[k] = ""

        elif isinstance(v, (str, int, float, bool)):
            safe[k] = v

        elif isinstance(v, list):
            safe[k] = ",".join(map(str, v))[:1000]

        elif isinstance(v, dict):
            safe[k] = json.dumps(v, ensure_ascii=False)[:1000]

        else:
            safe[k] = str(v)

    return safe


# =========================
# vector DB 연결
# =========================
def get_vector_store():

    embeddings = get_embedding_model()

    return Chroma(
        embedding_function=embeddings,
        persist_directory="app/data/embeddings"
    )


# =========================
# 1) resume 존재 여부 확인
# =========================
def check_resume_exists(resume_id: int):

    vector_store = get_vector_store()

    result = vector_store.get(
        ids=[str(resume_id)]
    )

    return result and len(result.get("ids", [])) > 0


# =========================
# 2) resume 저장 (기존)
# =========================
def save_to_vector_db(
    semantic_text: str,
    analysis_result: dict,
    resume_id: int
):

    vector_store = get_vector_store()

    safe_analysis = safe_metadata(analysis_result)

    metadata = {
        "resume_id": resume_id,
        **safe_analysis
    }

    document = Document(
        page_content=semantic_text,
        metadata=metadata
    )

    vector_store.add_documents(
        documents=[document],
        ids=[str(resume_id)]
    )

    try:
        vector_store.persist()
    except:
        pass

    print("✅ vector DB 저장 완료")

    return vector_store


# =========================
# 3) 핵심: 중복 방지 wrapper
# =========================
def save_resume_if_not_exists(
    semantic_text: str,
    analysis_result: dict,
    resume_id: int
):

    if check_resume_exists(resume_id):
        print(f"⚠️ resume_id {resume_id} 이미 존재 → 저장 스킵")
        return None

    print(f"🆕 resume_id {resume_id} 신규 저장")

    return save_to_vector_db(
        semantic_text,
        analysis_result,
        resume_id
    )

# =========================
# Resume와 유사한 Job Top5 조회
# =========================
def search_similar_jobs(
    semantic_text: str,
    resume_id: int,
    top_k: int = 5
):

    embeddings = get_embedding_model()

    job_vector_store = Chroma(
        embedding_function=embeddings,
        persist_directory="app/data/vectors/job_vectors"
    )

    results = job_vector_store.similarity_search_with_score(
        semantic_text,
        k=top_k
    )

    if not results:
        print("검색 결과 없음 → 빈 배열 반환")
        return []

    scores = [
        score
        for _, score in results
    ]

    max_score = max(scores)
    min_score = min(scores)

    print("================================")
    print("검색 결과 개수 :", len(results))
    print("================================")

    job_matches = []

    for document, score in results:

        print("=================")
        print("score =", score)
        print(document.metadata)

        if max_score == min_score:

            similarity = 50

        else:

            similarity = round(
                (
                    max_score - score
                )
                /
                (
                    max_score - min_score
                )
                * 100,
                2
            )

        print("similarity =", similarity)

        job_matches.append({

            "resume_id": resume_id,

            "job_posting_id": document.metadata.get(
                "job_posting_id"
            ),

            "similarity": similarity

        })

    print("job_matches =")
    print(job_matches)

    return job_matches
    