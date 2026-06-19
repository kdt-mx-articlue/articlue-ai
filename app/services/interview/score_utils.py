def clamp_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0

    if score < 0:
        return 0.0

    if score > 100:
        return 100.0

    return round(score, 2)


def avg_score(*scores: float) -> float:
    valid_scores = [clamp_score(score) for score in scores]

    if not valid_scores:
        return 0.0

    return round(sum(valid_scores) / len(valid_scores), 2)