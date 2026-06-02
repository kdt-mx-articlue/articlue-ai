import json

from app.services.candidate.candidate_json_service import (
    process_candidate_json
)

from app.services.vector.resume_vector_service import (
    save_resume_vector
)


JSON_PATH = (
    "app/data/docs/resume_002.json"
)

OUTPUT_PATH = (
    "app/data/outputs/"
    "parsed_candidate.json"
)


def main():

    # =========================
    # 이력서 분석
    # =========================
    result = process_candidate_json(
        JSON_PATH
    )

    # =========================
    # Vector DB 저장
    # =========================
    save_resume_vector(
        resume_data=result["resume_data"],
        analysis_result=result["analysis_result"]
    )

    # =========================
    # JSON 저장
    # =========================
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

    print(
        "벡터 저장 완료: "
        "app/data/vectors/resume_vectors"
    )


if __name__ == "__main__":
    main()