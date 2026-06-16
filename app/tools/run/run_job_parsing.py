import json

from app.services.jobs.job_service import (
    process_job_postings
)

from app.services.vector.job_vector_service import (
    save_job_vectors
)


EXCEL_PATH = (
    "app/data/raw/articlue_job_postings_datase.xlsx"
)

OUTPUT_PATH = (
    "app/data/outputs/"
    "parsed_jobs.json"
)


def main():

    # =========================
    # 채용공고 파싱
    # =========================
    results = process_job_postings(
    EXCEL_PATH
)

    print("111111111111111")

    save_job_vectors(
        results
    )

    print("222222222222222")
 

    # =========================
    # JSON 저장
    # =========================
    with open(
        OUTPUT_PATH,
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
        f"저장 완료: {OUTPUT_PATH}"
    )

    print(
        "벡터 저장 완료: "
        "app/data/vectors/job_vectors"
    )


if __name__ == "__main__":
    main()