def extract_developer_traits(
    github_data
):

    traits = []

    commits = github_data.get(
        "commits",
        []
    )

    text = " ".join(commits)

    if "refactor" in text:
        traits.append(
            "구조 개선 선호"
        )

    if "test" in text:
        traits.append(
            "테스트 지향"
        )

    if "fix" in text:
        traits.append(
            "문제 해결 중심"
        )

    if "FastAPI" in text:
        traits.append(
            "백엔드 중심"
        )

    if "LangChain" in text:
        traits.append(
            "AI 서비스 개발"
        )

    return traits