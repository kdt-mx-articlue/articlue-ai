import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.jobs import job_store
from app.services.jobs.job_service import parse_job
from app.services.vector.job_vector_service import (
    remove_job_vectors,
    upsert_job_vectors
)

router = APIRouter()

# 수집 배치에서만 호출 — 동시에 두 번 실행되지 않도록 직렬화 (파일·벡터 쓰기 충돌 방지)
_ingest_lock = threading.Lock()

# LLM 파싱 동시 호출 수 (응답 대기 위주라 CPU 부담은 작음)
PARSE_WORKERS = 3


class JobIngestRequest(BaseModel):
    jobs: List[Dict[str, Any]] = []
    remove_ids: List[int] = []


def _parse_safely(job):
    try:
        return parse_job(job), None
    except Exception as e:
        return None, {"job_posting_id": job.get("job_posting_id"), "error": str(e)}


# =========================
# 신규·변경 공고 반영 / 마감 공고 제거
# - 전달된 공고만 LLM 파싱 → 저장소 + 벡터에 추가/갱신 (전체 재파싱 없음)
# =========================
@router.post("/jobs/ingest")
def ingest_jobs(req: JobIngestRequest):

    with _ingest_lock:

        parsed_jobs = []
        failed = []

        if req.jobs:
            with ThreadPoolExecutor(max_workers=PARSE_WORKERS) as pool:
                for parsed, error in pool.map(_parse_safely, req.jobs):
                    if parsed:
                        parsed_jobs.append(parsed)
                    else:
                        failed.append(error)

        if parsed_jobs:
            # 벡터 먼저 반영 → 실패하면 저장소도 갱신하지 않음 (배치가 다음 실행에 재시도)
            upsert_job_vectors(parsed_jobs)
            job_store.upsert_jobs(parsed_jobs)

        removed_ids = []

        if req.remove_ids:
            remove_job_vectors(req.remove_ids)
            removed_ids = job_store.remove_jobs(req.remove_ids)

        print(f"[JobIngest] 반영 {len(parsed_jobs)}건 / 실패 {len(failed)}건 / 제거 {len(req.remove_ids)}건")

        return {
            "success": True,
            "ingested_ids": [job["job_posting_id"] for job in parsed_jobs],
            "failed": failed,
            "removed_ids": removed_ids,
        }
