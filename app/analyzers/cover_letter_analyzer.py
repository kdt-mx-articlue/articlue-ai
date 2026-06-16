def load_cover_letters(resume_data: dict):

    # 1. API 구조 or DB 구조 둘 다 대응
    cover_letters = []

    if isinstance(resume_data, dict):

        cover_letters = (
            resume_data.get("data", {}).get("coverLetters")
            or resume_data.get("coverLetters")
            or []
        )

    texts = []

    for cl in cover_letters or []:

        if not isinstance(cl, dict):
            continue

        items = cl.get("items", [])

        if not isinstance(items, list):
            continue

        for item in items:

            if not isinstance(item, dict):
                continue

            content = item.get("content")

            if isinstance(content, str) and content.strip():
                texts.append(content.strip())

    return texts