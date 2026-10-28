import re
from datetime import date

# =========================
# 경력 요건 체크
#
# 공고 최소 경력이 이력서 경력보다 CAREER_GAP_ALLOWANCE 년을 넘게 높으면 "경력 요건 미달"
#  - 예: 신입(0년) 지원자 → 2년 이상 공고까지는 지원 가능, 3년 이상부터 미달
# 미달 공고는 점수를 CAREER_MISMATCH_FACTOR 배로 깎아 상위 추천에 오르지 않게 한다
# =========================
CAREER_GAP_ALLOWANCE = 2
CAREER_MISMATCH_FACTOR = 0.4

# 개발 경력으로 보지 않는 직책
NON_DEV_POSITIONS = ("아르바이트", "알바", "파트타임")

_YEARS_PATTERN = re.compile(r"(\d+)\s*(?:년|[-~]\s*\d+\s*년)")


def parse_required_years(text):
    """
    공고 경력 조건 → 최소 요구 연차 (판단 불가면 None)
      "3년 이상" → 3, "5~10년" / "경력 5-10년" → 5, "경력 (3년이상)" → 3
      "신입", "신입·경력", "신입-경력 3~5년", "경력무관" → 0
      "경력", "공고문 내 명시 없음", "" → None
    """
    if not text:
        return None

    value = str(text)

    if "신입" in value or "무관" in value:
        return 0

    match = _YEARS_PATTERN.search(value)
    if match:
        return int(match.group(1))

    return None


def _months_between(start_ym, end_ym):
    try:
        sy, sm = map(int, str(start_ym)[:7].split("-"))
        if end_ym:
            ey, em = map(int, str(end_ym)[:7].split("-"))
        else:
            today = date.today()
            ey, em = today.year, today.month
        return max(0, (ey - sy) * 12 + (em - sm) + 1)
    except (ValueError, TypeError):
        return 0


def calculate_resume_years(careers):
    """
    이력서 경력(careers: startYm/endYm) 합산 연차. 아르바이트 등은 제외
    """
    months = 0

    for career in careers or []:
        position = str(career.get("position") or "")
        if any(keyword in position for keyword in NON_DEV_POSITIONS):
            continue
        months += _months_between(career.get("startYm"), career.get("endYm"))

    return round(months / 12, 1)


def check_career(job, resume_years):
    """
    공고 1건의 경력 요건 판정
    → {"required_years": int|None, "resume_years": float, "mismatch": bool}
    """
    parsed = job.get("parsed_result") or {}
    required = parse_required_years(parsed.get("career_level"))
    if required is None:
        required = parse_required_years(job.get("career_level"))

    mismatch = required is not None and required > resume_years + CAREER_GAP_ALLOWANCE

    return {
        "required_years": required,
        "resume_years": resume_years,
        "mismatch": mismatch,
    }
