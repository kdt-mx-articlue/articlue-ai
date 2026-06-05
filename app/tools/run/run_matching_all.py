import json

from app.services.candidate.candidate_json_service import (
    process_candidate_json
)

from app.services.matching.matching_service import (
    match_candidate_to_jobs
)

from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
import os


RESUME_PATH = "app/data/docs/resume_001.json"
JOB_PATH = "app/data/parsed/job_postings_parsed.json"
OUTPUT_PATH = "app/data/outputs/matching_results_all.json"

VECTOR_PATH = "app/data/vectors/matching_vectors"


# =========================
# Chroma init
# =========================
os.makedirs(VECTOR_PATH, exist_ok=True)

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(
    path=VECTOR_PATH
)

collection = chroma_client.get_or_create_collection(
    name="job_vectors"
)


def save_jobs_to_chroma(jobs_data):

    texts = []
    ids = []
    metadatas = []

    for job in jobs_data:

        parsed = job.get("parsed_result", {})

        text = (
            f"{parsed.get('role','')} "
            + " ".join(parsed.get("required_skills", []))
            + " ".join(parsed.get("preferred_skills", []))
        )

        texts.append(text)
        ids.append(str(job.get("job_id", len(ids))))
        metadatas.append({
            "company": job.get("company_name", ""),
            "title": job.get("job_title", "")
        })

    embeddings = embedding_model.embed_documents(texts)

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )


def main():

    # 1. 이력서 분석
    candidate_data = process_candidate_json(RESUME_PATH)

    # 2. 채용공고 로드
    with open(JOB_PATH, "r", encoding="utf-8") as f:
        jobs_data = json.load(f)

    # 3. 매칭
    results = match_candidate_to_jobs(
        candidate_data,
        jobs_data
    )

    # 4. 결과 저장 (기존 유지)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 5. 🔥 Chroma DB 저장 (추가)
    save_jobs_to_chroma(jobs_data)

    print(f"매칭 완료 + 벡터 저장 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()