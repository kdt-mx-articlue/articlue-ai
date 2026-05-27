import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def clean_json_response(text: str):

    """
    GPT markdown json 제거
    """

    text = text.strip()

    if text.startswith("```json"):
        text = text.replace(
            "```json",
            ""
        )

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def analyze_cover_letter(
    merged_text: str
):

    """
    자기소개서 semantic 분석
    """

    with open(
        "app/prompts/cover_letter_prompt.txt",
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
        "cover_letter": merged_text
    })

    try:

        cleaned_text = clean_json_response(
            response.content
        )

        parsed_result = json.loads(
            cleaned_text
        )

        return parsed_result

    except Exception as e:

        return {
            "error": str(e),
            "raw_response": response.content
        }


def analyze_job_posting(
    job_text: str
):

    """
    채용공고 semantic 분석
    """

    with open(
        "app/prompts/job_posting_prompt.txt",
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
        "job_posting": job_text
    })

    try:

        cleaned_text = clean_json_response(
            response.content
        )

        parsed_result = json.loads(
            cleaned_text
        )

        return parsed_result

    except Exception as e:

        return {
            "error": str(e),
            "raw_response": response.content
        }