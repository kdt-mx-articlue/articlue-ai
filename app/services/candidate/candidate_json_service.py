import json

from app.analyzers.semantic_extraction import (
    analyze_cover_letter
)


def process_candidate_json(
    json_path: str
):

    # =========================
    # JSON 로드
    # =========================
    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    # =========================
    # 벡터 분석용 텍스트 생성
    # =========================
    tech_stack = []

    for tech in data.get(
        "resume_tech_stack",
        []
    ):

        tech_stack.append(
            tech.get(
                "tech_name",
                ""
            )
        )

    merged_text = f"""
    이름:
    {
        data.get(
            "resume",
            {}
        ).get(
            "name",
            ""
        )
    }

    학력:
    {
        data.get(
            "education",
            []
        )
    }

    기술스택:
    {", ".join(tech_stack)}

    자기소개서:
    {
        data.get(
            "cover_letter",
            []
        )
    }
    """

    # =========================
    # LLM 분석
    # =========================
    result = analyze_cover_letter(
        merged_text
    )

    # =========================
    # 최종 반환
    # =========================
    return {

        "resume_data":
        data,

        "analysis_result":
        result
    }