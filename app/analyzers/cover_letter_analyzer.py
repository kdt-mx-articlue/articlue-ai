import json


def load_cover_letters(path: str):

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["cover_letter"]


def combine_cover_letters(cover_letters):

    merged_text = ""

    for item in cover_letters:

        merged_text += f"""
        [소제목]
        {item['sub_title']}

        [내용]
        {item['content']}
        """

    return merged_text