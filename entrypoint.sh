#!/bin/sh
set -e

VECTOR_DIR="app/data/vectors/job_vectors"

echo "===== Articlue AI Server 시작 ====="

# 벡터 DB가 없으면 job 파싱 먼저 실행
if [ ! -d "$VECTOR_DIR" ]; then
    echo "벡터 DB 없음 → job 파싱 실행 중..."
    python -m app.tools.run.run_job_parsing
    echo "job 파싱 완료"
else
    echo "벡터 DB 존재 → 파싱 스킵"
fi

echo "FastAPI 서버 시작..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5000
