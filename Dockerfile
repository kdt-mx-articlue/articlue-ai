FROM python:3.12-slim

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

# 소스 + 데이터 복사 (xlsx, 벡터 DB 포함)
COPY . .

EXPOSE 5000

# entrypoint: 벡터 DB 없으면 job 파싱 후 서버 시작
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
