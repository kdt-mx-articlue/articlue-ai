FROM python:3.12-slim

WORKDIR /code

# 컴파일 도구 설치 (curl: healthcheck용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (빠른 Python 패키지 매니저)
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

# 가상 환경 생성
RUN uv venv .venv

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="/code/.venv/bin:$PATH"
ENV HF_HOME=/code/.cache/huggingface

# torch는 CPU 전용 빌드로 먼저 설치 (기본 CUDA 빌드는 수 GB라 이미지가 과도하게 커짐)
RUN uv pip install --no-cache torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu

# 의존성 설치 (소스 변경과 캐시 분리)
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt

# 임베딩 모델 사전 다운로드 (컨테이너 기동 시 다운로드 대기 제거)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# 소스 + 데이터 복사 (xlsx, 벡터 DB 포함)
COPY . .

EXPOSE 5000

# entrypoint: 벡터 DB 없으면 job 파싱 후 서버 시작
COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
