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

    # 백엔드 응답이 success/message/data 구조인 경우 대응
    resume_data = data.get(
        "data",
        data
    )

    return process_candidate_json_data(
        resume_data
    )


# =========================
# 백엔드(dict) 기반 처리
# =========================
def process_candidate_json_data(data: dict):

    # =========================
    # 기술스택
    # =========================
    tech_stack = [

        tech.get(
            "techName",
            ""
        )

        for tech in data.get(
            "techStacks",
            []
        )

    ]

    # =========================
    # 자기소개서 병합
    # =========================
    cover_letter_text = "\n".join(

        [

            item.get(
                "content",
                ""
            )

            for cover in data.get(
                "coverLetters",
                []
            )

            for item in cover.get(
                "items",
                []
            )

        ]

    )

    # =========================
    # LLM 입력 텍스트
    # =========================
    merged_text = f"""
이름:
{data.get("profile", {}).get("name", "")}

희망직무:
{data.get("desiredJob", "")}

자기소개:
{data.get("introduction", "")}

학력:
{data.get("educations", [])}

기술스택:
{", ".join(tech_stack)}

프로젝트 및 활동:
{data.get("experiences", [])}

경력:
{data.get("careers", [])}

자격증:
{data.get("certificates", [])}

자기소개서:
{cover_letter_text}
""".strip()

    # =========================
    # LLM 분석
    # =========================
    analysis_result = analyze_cover_letter(
        merged_text
    )

    
    # GitHub 분석
    # =========================
    # =========================

    github_traits = extract_developer_traits(
        data
    )

    github_profile = build_github_profile(
        data
    )

    # =========================
    # STAR 분석
    # =========================
    star_results = []

    for cover in data.get(
        "coverLetters",
        []
    ):

        for item in cover.get(
            "items",
            []
        ):

            star_results.append(

                {

                    "sub_title":

                    item.get(
                        "subTitle",
                        ""
                    ),

                    "star_analysis":

                    analyze_star_structure(

                        item.get(
                            "content",
                            ""
                        )

                    )

                }

            )

    # =========================
    # 최종 반환
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