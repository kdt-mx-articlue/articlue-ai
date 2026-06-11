def build_github_profile(resume):

    repos = resume.get("githubRepositories", [])

    # =========================
    # 1. repo 수
    # =========================
    repo_count = len(repos)

    # =========================
    # 2. commit 수 (daily 집계 기반)
    # =========================
    commit_count = 0

    for repo in repos:
        for daily in repo.get("commitDaily", []):
            commit_count += daily.get("commitCount", 0)

    # =========================
    # 3. activity score (정규화된 점수)
    # =========================
    # repo는 프로젝트 다양성
    # commit은 실제 활동량
    activity_score = min(
        100,
        repo_count * 15 +     # 프로젝트 다양성 가중치 ↑
        commit_count * 2      # 커밋 활동 반영
    )

    # =========================
    # 4. 추가 지표 (추천)
    # =========================

    total_days = 0

    for repo in repos:
        total_days += len(repo.get("commitDaily", []))

    avg_commits_per_day = (
        commit_count / total_days
        if total_days > 0 else 0
    )

    return {
        "repo_count": repo_count,
        "commit_count": commit_count,
        "activity_score": activity_score,
        "avg_commits_per_day": round(avg_commits_per_day, 2)
    }