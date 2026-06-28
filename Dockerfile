FROM python:3.11-slim

WORKDIR /code

# 컴파일 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv 설치 (빠른 Python 패키지 매니저)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 가상 환경 생성
RUN uv venv .venv

ENV VIRTUAL_ENV=/code/.venv
ENV PATH="/code/.venv/bin:$PATH"

# 의존성 설치 (소스 변경과 캐시 분리)
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt

# 소스 복사
COPY . .

EXPOSE 5000

# 배포 환경 — --reload 없음, private 서버에서만 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
