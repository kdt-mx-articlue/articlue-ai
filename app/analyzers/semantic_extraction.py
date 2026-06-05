import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


# =========================
# JSON 안전 처리
# =========================
def clean_json_response(text: str):

    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "")

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# =========================
# LLM 공통 실행
# =========================
def run_llm(prompt_path: str, input_key: str, input_text: str):

    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    prompt = ChatPromptTemplate.from_template(prompt_text)

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

    chain = prompt | llm

    response = chain.invoke({
        input_key: input_text
    })

    try:
        cleaned = clean_json_response(response.content)
        return json.loads(cleaned)

    except Exception as e:
        return {
            "error": str(e),
            "raw_response": response.content
        }


# =========================
# 자기소개서 분석
# =========================
def analyze_cover_letter(merged_text: str):

    return run_llm(
        "app/prompts/cover_letter_prompt.txt",
        "cover_letter",
        merged_text
    )

def analyze_star_structure(
    cover_letter_text: str
):

    with open(
        "app/prompts/star_analysis_prompt.txt",
        "r",
        encoding="utf-8"
    ) as f:

        prompt_text = f.read()

    prompt = ChatPromptTemplate.from_template(
        prompt_text
    )

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

    chain = prompt | llm

    response = chain.invoke({
        "cover_letter": cover_letter_text
    })

    try:

        cleaned_text = clean_json_response(
            response.content
        )

        return json.loads(
            cleaned_text
        )

    except Exception as e:

        return {
            "error": str(e),
            "raw_response": response.content
        }

# =========================
# 채용공고 분석
# =========================
def analyze_job_posting(job_text: str):

    result = run_llm(
        "app/prompts/job_posting_prompt.txt",
        "job_posting",
        job_text
    )

    return result



# =========================
# (옵션) resume 분석용 확장 구조
# =========================
def analyze_resume(resume_text: str):

    result = run_llm(
        "app/prompts/resume_prompt.txt",
        "resume",
        resume_text
    )

    return result