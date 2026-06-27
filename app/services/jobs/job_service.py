import csv
import json
import os

import pandas as pd

from app.analyzers.semantic_extraction import (
    analyze_job_posting
)

CSV_FIELDS = [
    "job_posting_id",
    "company_name",
    "job_title",
    "career_level",
    "deadline",
    "apply_url",
    "tech_stacks",
    "requirements",
    "preferences",
    "responsibilities",
    "team_culture",
    "benefits",
]


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
        {row.get("preferences", "")}

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
            "job_posting_id":   idx,
            "company_name":     row.get("company_name",     ""),
            "job_title":        row.get("job_title",        ""),
            "career_level":     row.get("career_level",     ""),
            "deadline":         row.get("deadline",         ""),
            "apply_url":        row.get("apply_url",        ""),
            "tech_stacks":      row.get("tech_stacks",      ""),
            "requirements":     row.get("requirements",     ""),
            "preferences":      row.get("preferences",      ""),
            "responsibilities": row.get("responsibilities", ""),
            "team_culture":     row.get("team_culture",     ""),
            "benefits":         row.get("benefits",         ""),
            "parsed_result":    result,
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

    # =========================
    # CSV 저장 (job_posting_id 포함)
    # JOB_CSV_PATH 환경변수로 경로 지정 가능
    # (Docker Compose: 프론트엔드 public 폴더를 마운트해서 직접 갱신)
    # =========================
    csv_path = os.environ.get(
        "JOB_CSV_PATH",
        "app/data/outputs/job_postings.csv"
    )

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(results)

    print(
        f"CSV 저장 완료: {csv_path}"
    )

    print(
        f"총 {len(results)}개 처리 완료"
    )

    return results




def get_all_jobs():
    """
    전체 채용공고를 {job_posting_id: job} 딕셔너리로 반환 (파일 1회 로드)
    """
    with open(
        "app/data/job_postings_parsed.json",
        "r",
        encoding="utf-8"
    ) as f:
        jobs = json.load(f)

    return {job["job_posting_id"]: job for job in jobs}


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