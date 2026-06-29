#!/bin/sh
set -e

VECTOR_FILE="app/data/vectors/job_vectors/chroma.sqlite3"

echo "===== Articlue AI Server 시작 ====="

# 벡터 DB 실제 데이터가 없으면 job 파싱 먼저 실행
if [ ! -f "$VECTOR_FILE" ]; then
    echo "벡터 DB 없음 → job 파싱 실행 중..."
    python -m app.tools.run.run_job_parsing
    echo "job 파싱 완료"
else
    echo "벡터 DB 존재 → 파싱 스킵"
fi

echo "FastAPI 서버 시작..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5000
