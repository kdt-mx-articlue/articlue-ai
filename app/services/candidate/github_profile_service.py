def build_github_profile(
    github_data
):

    repo_count = len(
        github_data.get(
            "repos",
            []
        )
    )

    commit_count = len(
        github_data.get(
            "commits",
            []
        )
    )

    activity_score = min(
        100,
        repo_count * 10 +
        commit_count * 3
    )

    return {

        "repo_count":
        repo_count,

        "commit_count":
        commit_count,

        "activity_score":
        activity_score
    }