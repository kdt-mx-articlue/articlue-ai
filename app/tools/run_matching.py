import json

from app.services.matching_service import (
    match_candidate_to_jobs
)


OUTPUT_PATH = (
    "app/data/outputs/"
    "matching_results.json"
)


def main():

    results = match_candidate_to_jobs()

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
        f"매칭 완료: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()