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
    for idx, (_, row) in enumerate(
    df.iterrows(),
    start=1
):

        merged_text = f"""
        회사명:
        {row.get("company_name", "")}

        직무:
        {row.get("job_title", "")}

        경력조건:
        {row.get("career_level", "")}

        자격요건:
        {row.get("requirements", "")}

        우대사항:
        {row.get("preference", "")}

        주요업무:
        {row.get("responsibilities", "")}

        기술스택:
        {row.get("tech_stacks", "")}

        인재상:
        {row.get("team_culture", "")}

        복지혜택:
        {row.get("benefits", "")}
         """.strip()
        

        # =====================
        # 채용공고 LLM 분석
        # =====================
        result = analyze_job_posting(
            merged_text
        )

        parsed_job = {

        "job_posting_id": idx,

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
            f"[완료] {idx}번째 채용공고 분석 완료"
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




def get_job_by_id(job_id):

    with open(

        "app/data/job_postings_parsed.json",

        "r",

        encoding="utf-8"

    ) as f:

        jobs = json.load(f)

    for job in jobs:

        if job["job_posting_id"] == job_id:

            return job

    return None