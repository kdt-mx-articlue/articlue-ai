import json
import pandas as pd

from app.analyzers.semantic_extraction import (
    analyze_job_posting
)


def process_job_postings(
    excel_path: str
):

    """
    채용공고 전체 처리
    + LLM 분석
    + JSON 저장
    """

    # =========================
    # 엑셀 로드
    # =========================
    df = pd.read_excel(
        excel_path
    )

    # NaN 제거
    df = df.fillna("")

    results = []

    # =========================
    # 전체 row 처리
    # =========================
    for idx, row in df.iterrows():

        merged_text = f"""
        회사명:
        {row.get("company_name", "")}

        직무:
        {row.get("job_title", "")}

        requirements:
        {row.get("requirements", "")}

        preferences:
        {row.get("preferences", "")}

        responsibilities:
        {row.get("responsibilities", "")}

        tech_stacks:
        {row.get("tech_stacks", "")}

        team_culture:
        {row.get("team_culture", "")}
        """

        # =====================
        # 채용공고 LLM 분석
        # =====================
        result = analyze_job_posting(
            merged_text
        )

        parsed_job = {

            "job_id": idx,

            "company_name": row.get(
                "company_name",
                ""
            ),

            "job_title": row.get(
                "job_title",
                ""
            ),

            "parsed_result": result
        }

        results.append(
            parsed_job
        )

        print(
            f"[완료] {idx + 1}번째 채용공고 분석 완료"
        )

    # =========================
    # JSON 저장
    # =========================
    save_path = (
        "app/data/job_postings_parsed.json"
    )

    with open(
        save_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\n채용공고 저장 완료: {save_path}"
    )

    print(
        f"총 {len(results)}개 처리 완료"
    )

    return results