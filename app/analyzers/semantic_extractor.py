from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def analyze_cover_letter(merged_text: str):

    """
    자기소개서 semantic 분석
    """

    # Prompt 로드
    with open(
        "app/prompts/cover_letter_prompt.txt",
        "r",
        encoding="utf-8"
    ) as f:

        prompt_text = f.read()

    # Prompt Template 생성
    prompt = ChatPromptTemplate.from_template(prompt_text)

    # LLM 생성
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

    # Chain 생성
    chain = prompt | llm

    # 분석 실행
    response = chain.invoke({
        "cover_letter": merged_text
    })

    return response.content