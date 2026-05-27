import pandas as pd

from app.analyzers.semantic_extraction import (
    analyze_job_posting
)


def process_job_postings(
    excel_path: str
):

    """
    채용공고 전체 처리
    """

    # 엑셀 로드
    df = pd.read_excel(excel_path)

    results = []

    for idx, row in df.head(1).iterrows():

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

        result = analyze_job_posting(
            merged_text
        )

        results.append({
            "company_name": row.get(
                "company_name"
            ),
            "job_title": row.get(
                "job_title"
            ),
            "parsed_result": result
        })

    return results