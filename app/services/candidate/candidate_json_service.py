import json

from app.analyzers.semantic_extraction import (
    analyze_cover_letter,
    analyze_star_structure
)

from app.services.candidate.github_analyzer import (
    extract_developer_traits
)

from app.services.candidate.github_profile_service import (
    build_github_profile
)


# =========================
# JSON 파일 기반 처리
# =========================
def process_candidate_json(json_path: str):

    with open(
        json_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return process_candidate_data(data)


# =========================
# 백엔드(dict) 기반 처리
# =========================
def process_candidate_data(data: dict):

    # =========================
    # 기술스택
    # =========================
    tech_stack = [
        tech.get("tech_name", "")
        for tech in data.get(
            "resume_tech_stack",
            []
        )
    ]

    # =========================
    # 자기소개서 병합
    # =========================
    cover_letter_text = "\n".join([
        item.get(
            "content",
            ""
        )
        for item in data.get(
            "cover_letter",
            []
        )
    ])

    # =========================
    # LLM 입력 텍스트
    # =========================
    merged_text = f"""
이름:
{data.get("resume", {}).get("name", "")}

학력:
{data.get("education", [])}

기술스택:
{", ".join(tech_stack)}

자기소개서:
{cover_letter_text}
""".strip()

    # =========================
    # LLM 분석
    # =========================
    analysis_result = analyze_cover_letter(
        merged_text
    )

    # =========================
    # GitHub 분석
    # =========================
    github = data.get(
        "github",
        {}
    )

    github_traits = extract_developer_traits(
        github
    )

    github_profile = build_github_profile(
        github
    )

    # =========================
    # STAR 분석
    # =========================
    star_results = []

    for item in data.get(
        "cover_letter",
        []
    ):

        star_results.append({

            "sub_title":
            item.get(
                "sub_title",
                ""
            ),

            "star_analysis":
            analyze_star_structure(
                item.get(
                    "content",
                    ""
                )
            )
        })

    # =========================
    # 반환
    # =========================
    return {

        "resume_data":
        data,

        "analysis_result":
        analysis_result,

        "star_analysis":
        star_results,

        "github_traits":
        github_traits,

        "github_profile":
        github_profile
    }