from app.services.matching.scoring import calculate_score

from app.services.matching_features import (
    build_features
)

from app.services.semantic_matcher import (
    calculate_semantic_score
)


def rank_jobs(candidate_result, job_list):

    results = []

    for job in job_list:

        # =========================
        # feature 생성
        # =========================
        features = build_features(
            candidate_result,
            job
        )

        # =========================
        # semantic score 계산
        # =========================
        job_text = job.get(
            "job_description",
            ""
        )

        semantic_score = (
            calculate_semantic_score(
                job_text
            )
        )

        # =========================
        # feature에 추가
        # =========================
        features["semantic_score"] = (
            semantic_score
        )

        # =========================
        # 최종 점수 계산
        # =========================
        score = calculate_score(
            features
        )

        results.append({

            "job_id": job["id"],

            "score": score,

            "features": features
        })

    return sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )