import json

from app.services.candidate_json_service import (
    process_candidate_json
)


JSON_PATH = (
    "app/data/docs/resume_003.json"
)

OUTPUT_PATH = (
    "app/data/outputs/"
    "parsed_candidate.json"
)


def main():

    result = process_candidate_json(
        JSON_PATH
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"저장 완료: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()