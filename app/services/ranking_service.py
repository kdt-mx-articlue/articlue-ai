from app.services.scoring import calculate_score
from app.services.matching_features import build_features


def rank_jobs(candidate_result, job_list):

    results = []

    for job in job_list:

        features = build_features(candidate_result, job)

        score = calculate_score(features)

        results.append({
            "job_id": job["id"],
            "score": score,
            "features": features
        })

    return sorted(results, key=lambda x: x["score"], reverse=True)