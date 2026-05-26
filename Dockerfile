FROM python:3.11-slim
WORKDIR /code

# ChromaDB 및 의존성 라이브러리 컴파일을 위한 필수 도구 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

EXPOSE 5000
# 소스코드 변경 시 실시간 반영되도록 --reload 옵션 부여
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]