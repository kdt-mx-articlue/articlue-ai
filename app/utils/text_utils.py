from typing import Optional


def normalize_text(value: Optional[str]) -> str:
    if value is None:
        return ""

    return " ".join(str(value).split())


def truncate_text(value: Optional[str], max_length: int = 8000) -> str:
    text = normalize_text(value)

    if len(text) <= max_length:
        return text

    return text[:max_length] + "\n...(내용 일부 생략)"


def safe_join(parts: list[str], separator: str = "\n") -> str:
    valid_parts = [
        normalize_text(part)
        for part in parts
        if normalize_text(part)
    ]

    return separator.join(valid_parts)