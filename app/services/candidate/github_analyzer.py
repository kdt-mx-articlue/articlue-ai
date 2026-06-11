def extract_developer_traits(resume):

    traits = []

    # =========================
    # 1. Tech Stack 기반
    # =========================
    tech_stacks = resume.get("techStacks", [])
    repo_list = resume.get("githubRepositories", [])

    tech_names = {
        t.get("techName", "").lower()
        for t in tech_stacks
    }

    framework_names = {
        t.get("techName", "").lower()
        for t in tech_stacks
        if t.get("techCategoryName") == "framework"
    }

    db_names = {
        t.get("techName", "").lower()
        for t in tech_stacks
        if t.get("techCategoryName") == "database"
    }

    # 백엔드 중심
    if "express.js" in framework_names:
        traits.append("백엔드 중심")

    # DB 기반 개발
    if len(db_names) > 0:
        traits.append("데이터베이스 활용 개발")

    # =========================
    # 2. GitHub Repo 기술 기반
    # =========================
    repo_frameworks = set()
    repo_languages = set()

    for repo in repo_list:
        for t in repo.get("techStacks", []):
            repo_frameworks.add(t.get("techName", "").lower())
            repo_languages.add(t.get("languageName", "").lower())

    if "express.js" in repo_frameworks:
        traits.append("Node.js 기반 개발 경험")

    if "javascript" in repo_languages:
        traits.append("프론트/백엔드 JS 생태계 경험")

    # =========================
    # 3. 커밋 활동 기반 (정량 데이터)
    # =========================
    total_commits = 0

    for repo in repo_list:
        for d in repo.get("commitDaily", []):
            total_commits += d.get("commitCount", 0)

    if total_commits >= 50:
        traits.append("지속적인 개발 활동")

    elif total_commits >= 10:
        traits.append("개발 활동 경험 있음")

    # =========================
    # 4. 프로젝트 성격 기반
    # =========================
    for repo in repo_list:
        desc = (repo.get("description") or "").lower()

        if "backend" in desc or "api" in desc:
            traits.append("API 서버 개발 경험")

        if "oracle" in desc:
            traits.append("엔터프라이즈 DB 경험")

    return list(set(traits))