import json

from app.services.job_service import (
    process_job_postings
)


EXCEL_PATH = (
    "app/data/docs/articlue_job_postings_datase.xlsx"
)

OUTPUT_PATH = (
    "app/data/outputs/"
    "parsed_jobs.json"
)


def main():

    results = process_job_postings(
        EXCEL_PATH
    )

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


if __name__ == "__main__":
    main()