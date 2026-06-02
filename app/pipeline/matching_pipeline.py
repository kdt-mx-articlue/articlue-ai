import json
import os

from app.services.matching.matching import match_candidate_to_jobs
from app.services.vector.vector_store import save_to_vector_db


# =========================
# JSON 저장
# =========================
def save_to_json(data, filename="output/result.json"):

    os.makedirs("output", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =========================
# 🔥 PIPELINE (여기서 저장 담당)
# =========================
def run_matching_pipeline(candidate_data, jobs_data):

    # 1. matching (pure)
    results = match_candidate_to_jobs(candidate_data, jobs_data)

    # 2. JSON 저장
    save_to_json({
        "candidate": candidate_data,
        "results": results
    })

    # 3. Vector DB 저장
    save_to_vector_db(candidate_data, jobs_data)

    return results