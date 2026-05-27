import json

from app.analyzers.semantic_extraction import (
    analyze_cover_letter
)


def process_candidate_json(
    json_path: str
):

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    merged_text = f"""
    이름:
    {data.get("name", "")}

    학력:
    {data.get("education", "")}

    기술스택:
    {", ".join(data.get("skills", []))}

    프로젝트:
    {", ".join(data.get("projects", []))}

    자기소개서:
    {data.get("cover_letter", "")}
    """

    result = analyze_cover_letter(
        merged_text
    )

    return {
        "name": data.get(
        "resume",
        {}
        )       .get(
        "name",
        "unknown"
        ),
        "parsed_result": result
}