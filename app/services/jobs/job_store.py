import json
import os
import threading

# =========================
# 채용공고 파싱 결과 저장소
#
# - STORE_PATH : 도커 볼륨(app/data/vectors) 안 → 주간 수집으로 추가된 공고가 재시작 후에도 유지
# - SEED_PATH  : 이미지에 포함된 초기 484건 (STORE_PATH 가 아직 없을 때만 사용)
# - 파일 수정 시각이 바뀔 때만 다시 읽어 요청마다 JSON 전체를 읽지 않음
# =========================
STORE_PATH = os.environ.get(
    "JOB_STORE_PATH",
    "app/data/vectors/job_postings_parsed.json"
)

SEED_PATH = "app/data/job_postings_parsed.json"

_lock = threading.Lock()
_cache = {"path": None, "mtime": None, "jobs": {}}


def _current_path():
    return STORE_PATH if os.path.exists(STORE_PATH) else SEED_PATH


def load_jobs():
    """
    {job_posting_id: job} 반환 (캐시)
    """
    path = _current_path()
    mtime = os.path.getmtime(path)

    with _lock:
        if _cache["path"] != path or _cache["mtime"] != mtime:
            with open(path, "r", encoding="utf-8") as f:
                jobs = json.load(f)

            _cache.update(
                path=path,
                mtime=mtime,
                jobs={int(job["job_posting_id"]): job for job in jobs}
            )

        return _cache["jobs"]


def _write(jobs_by_id):
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)

    tmp_path = f"{STORE_PATH}.tmp"

    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(
            sorted(jobs_by_id.values(), key=lambda job: int(job["job_posting_id"])),
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(tmp_path, STORE_PATH)


def upsert_jobs(parsed_jobs):
    jobs = dict(load_jobs())

    for job in parsed_jobs:
        jobs[int(job["job_posting_id"])] = job

    _write(jobs)


def remove_jobs(job_ids):
    jobs = dict(load_jobs())
    removed = [job_id for job_id in map(int, job_ids) if jobs.pop(job_id, None) is not None]

    if removed:
        _write(jobs)

    return removed
