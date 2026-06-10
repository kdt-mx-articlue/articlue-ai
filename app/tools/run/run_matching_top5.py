import json
from pathlib import Path

from app.services.candidate.candidate_json_service import (
    process_candidate_json
)

from app.services.matching.matching_service import (
    calculate_matching_score,
    calculate_requirement_fit
)

from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb



# =========================
# 폴더 생성
# =========================
Path("app/data/outputs").mkdir(parents=True, exist_ok=True)
Path("app/data/vectors/job_vectors").mkdir(parents=True, exist_ok=True)


# =========================
# 파일 경로
# =========================
RESUME_PATH = "app/data/docs/resume_002.json"
JOB_PATH = "app/data/parsed/job_postings_parsed.json"
OUTPUT_PATH = "app/data/outputs/matching_results_top5.json"

VECTOR_PATH = "app/data/vectors/matching_vectors"


# =========================
# Chroma DB 세팅
# =========================
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(
    path=VECTOR_PATH
)

collection = chroma_client.get_or_create_collection(
    name="job_vectors"
)


# =========================
# Job Vector 저장 함수
# =========================
def save_jobs_to_chroma(jobs):

    texts = []
    ids = []
    metadatas = []

    for job in jobs:

        parsed = job.get(
            "parsed_result",
            {}
        )

        text = f"""
직무:
{job.get("job_title", "")}

기술스택:
{parsed.get("tech_stacks", "")}

자격요건:
{parsed.get("requirements", "")}

우대사항:
{parsed.get("preference", "")}

주요업무:
{parsed.get("responsibilities", "")}

인재상:
{parsed.get("team_culture", "")}

복지혜택:
{parsed.get("benefits", "")}
""".strip()

        texts.append(text)

        ids.append(
            str(
                job.get(
                    "job_id",
                    len(ids)
                )
            )
        )

        metadatas.append({
            "company":
            job.get(
                "company_name",
                ""
            ),

            "title":
            job.get(
                "job_title",
                ""
            )
        })

    embeddings = embedding_model.embed_documents(
        texts
    )

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )


# =========================
# MAIN
# =========================
def main():

    # =========================
    # 이력서 분석
    # =========================
    candidate_result = process_candidate_json(RESUME_PATH)

    # =========================
    # 채용공고 로드
    # =========================
    with open(JOB_PATH, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    # =========================
    # 매칭 점수 계산
    # =========================
    results = []

    for job in jobs:

     semantic_score = calculate_matching_score(
        candidate_result,
        job
    )

     requirement_fit = calculate_requirement_fit(
        candidate_result,
        job
    )

     github_profile = candidate_result.get(
        "github_profile",
        {}
    )

     github_score = round(
        github_profile.get(
            "activity_score",
            0
        ) / 100,
        4
    )

     final_score = round(
        semantic_score * 0.95
        +
        github_score * 0.05,
        4
    )

     results.append({

        "company_name":
        job.get(
            "company_name",
            ""
        ),

        "job_title":
        job.get(
            "job_title",
            ""
        ),

        "semantic_score":
        semantic_score,

        "github_score":
        github_score,

        "final_score":
        final_score,

        "requirement_fit":
        requirement_fit

    })

                



    # =========================
    # 점수 정렬
    # =========================
    results.sort(
        key=lambda x: x["final_score"],
        reverse=True
    )

    # =========================
    # TOP 5
    # =========================
    top5_results = results[:5]

    # =========================
    # 콘솔 출력
    # =========================
    print("\n🔥 TOP 5 MATCHING RESULTS\n")

    for idx, result in enumerate(top5_results, start=1):

        print(f"""
=========================
순위: {idx}

회사:
{result['company_name']}

직무:
{result['job_title']}

Semantic Score:
{result['semantic_score']}


GitHub Score:
{result['github_score']}

Final Score:
{result['final_score']}

=========================
""")

    # =========================
    # JSON 저장
    # =========================
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(top5_results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ TOP 5 저장 완료")
    print(f"📁 저장 위치: {OUTPUT_PATH}")

    # =========================
    # 🔥 Chroma DB 저장 (추가)
    # =========================
    save_jobs_to_chroma(jobs)

    print("\n🧠 Vector DB 저장 완료")


if __name__ == "__main__":
    main()