import json
import re
from typing import Any


class JsonParseError(ValueError):
    pass


def extract_json_object(raw_text: str) -> dict[str, Any]:
    if not raw_text:
        raise JsonParseError("LLM 응답이 비어 있습니다.")

    text = raw_text.strip()

    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start < 0 or end < 0 or start >= end:
        raise JsonParseError(f"JSON 객체를 찾지 못했습니다. 원문: {raw_text}")

    candidate = text[start:end + 1]

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise JsonParseError(f"JSON 파싱 실패: {exc}. 원문: {raw_text}") from exc

    if not isinstance(parsed, dict):
        raise JsonParseError("LLM 응답이 JSON object가 아닙니다.")

    return parsed