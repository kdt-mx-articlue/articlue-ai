import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ─── 기본 5문항 (공고에서 추출 실패 시 fallback) ──────────────
DEFAULT_QUESTIONS = [
    "지원 동기",
    "성장과정 및 가치관",
    "직무 관련 경험 및 역량",
    "팀 협업 및 갈등 해결 경험",
    "입사 후 포부 및 목표",
]


# ─── 1단계: 공고에서 자소서 문항 추출 ────────────────────────
def extract_questions(job_description: str) -> list[str] | None:
    """
    공고 텍스트에서 자소서 문항을 추출합니다.
    문항이 없거나 추출 불가 시 None 반환 → 호출부에서 DEFAULT_QUESTIONS 사용.
    """
    if not job_description or len(job_description.strip()) < 50:
        return None

    prompt = f"""아래 채용공고 텍스트에서 자기소개서 작성 문항을 추출해주세요.

[채용공고]
{job_description}

규칙:
- 공고에 명시된 자소서 문항만 추출하세요.
- 문항이 없으면 반드시 null을 반환하세요.
- 문항이 있으면 JSON 배열로 반환하세요. 예: ["지원동기", "직무경험", ...]
- 문항 텍스트는 원문 그대로 유지하세요.
- JSON 외 텍스트는 절대 포함하지 마세요.

응답 형식 (둘 중 하나):
{{"questions": ["문항1", "문항2", ...]}}
또는
{{"questions": null}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(response.choices[0].message.content)
        questions = parsed.get("questions")
        if isinstance(questions, list) and len(questions) > 0:
            return questions
        return None
    except Exception:
        return None


# ─── 이력서에서 범용 자소서 추출 ─────────────────────────────
def _extract_base_cover_letter(resume_data: dict) -> str:
    """
    사용자가 이력서에 작성한 범용 자소서를 추출합니다.
    여러 항목이 있으면 하나의 텍스트로 합쳐서 반환.
    """
    data = resume_data.get("data", resume_data)
    cover_letters = data.get("coverLetters", [])

    texts = []
    for cl in cover_letters:
        if not isinstance(cl, dict):
            continue
        for item in cl.get("items", []):
            if not isinstance(item, dict):
                continue
            q = item.get("question", "")
            content = item.get("content", "")
            if content and content.strip():
                if q:
                    texts.append(f"[{q}]\n{content.strip()}")
                else:
                    texts.append(content.strip())

    return "\n\n".join(texts) if texts else ""


# ─── 이력서 핵심 정보 요약 ────────────────────────────────────
def build_resume_summary(resume_data: dict) -> str:
    data = resume_data.get("data", resume_data)
    lines = []

    techs = data.get("techStacks", [])
    if techs:
        names = [t.get("techName", "") for t in techs if t.get("techName")]
        lines.append(f"기술스택: {', '.join(names)}")

    careers = data.get("careers", [])
    for c in careers:
        lines.append(
            f"경력: {c.get('companyName','')} / {c.get('jobTitle','')} "
            f"({c.get('startDate','')}~{c.get('endDate','')})"
        )

    activities = data.get("activities", [])
    for a in activities:
        lines.append(f"활동/프로젝트: {a.get('activityName', a.get('title', ''))}")

    education = data.get("educations", [])
    for e in education:
        lines.append(
            f"학력: {e.get('schoolName','')} {e.get('major','')} "
            f"({e.get('startDate','')}~{e.get('endDate','')})"
        )

    github = data.get("githubAccount", {})
    if github:
        repos = github.get("repositories", [])
        repo_names = [r.get("repoName", "") for r in repos[:3] if r.get("repoName")]
        if repo_names:
            lines.append(f"GitHub 주요 프로젝트: {', '.join(repo_names)}")

    return "\n".join(lines) if lines else "이력서 정보 없음"


# ─── 2단계: 자소서 재구성 생성 ───────────────────────────────
def _restructure(
    base_cover_letter: str,
    resume_summary: str,
    company_name: str,
    job_title: str,
    job_description: str,
    questions: list[str],
) -> list[dict]:
    """
    사용자의 범용 자소서와 이력서 정보를 바탕으로
    지정된 문항에 맞게 자소서를 재구성합니다.
    """
    has_base = bool(base_cover_letter.strip())

    system_prompt = """당신은 취업 자기소개서 전문 컨설턴트입니다.
지원자의 이력서 정보와 기존 자소서를 분석하여,
지원 기업/직무에 최적화된 자소서를 재구성합니다.

작성 원칙:
- 이력서와 기존 자소서에 실제로 있는 경험만 활용하세요. 없는 내용 지어내기 금지.
- 기술 스택, 숫자, 기간 등 구체적 사실을 그대로 사용하세요.
- 각 문항의 취지에 맞게 내용을 선별해서 재구성하세요.
- 기술 경험은 비즈니스 임팩트 언어로 서술하세요 (예: "API 개발" → "서비스 응답속도 개선으로 사용자 경험 향상").
- 인상적인 소제목(큰따옴표)으로 시작하고, 문항당 500~750자로 작성하세요.
- 자연스러운 한국어 존댓말, 능동형 서술 (하게 되었습니다 X → 했습니다 O).
- 반드시 JSON 배열로만 응답하세요.
"""

    base_section = f"""[지원자 기존 범용 자소서]
{base_cover_letter}

""" if has_base else "[기존 자소서 없음 - 이력서 정보만으로 작성]\n\n"

    user_prompt = f"""[지원 정보]
기업명: {company_name}
직무: {job_title}
공고 내용: {job_description or "정보 없음"}

[지원자 이력서 요약]
{resume_summary}

{base_section}[작성할 자소서 문항]
{json.dumps(questions, ensure_ascii=False)}

위 문항에 맞게 자소서를 {"재구성" if has_base else "작성"}해주세요.
{"기존 자소서의 핵심 경험을 살리되, 이 회사/직무에 맞게 강조점을 바꾸고 문항 구조에 맞게 재배치하세요." if has_base else ""}

반드시 아래 형태의 JSON으로만 응답하세요:
{{
  "items": [
    {{"question": "문항 텍스트", "answer": "답변 내용"}},
    ...
  ]
}}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )

    return _parse_items(response.choices[0].message.content, questions)


# ─── JSON 파싱 유틸 ───────────────────────────────────────────
def _parse_items(raw: str, questions: list[str]) -> list[dict]:
    parsed = json.loads(raw)

    if isinstance(parsed, list):
        items = parsed
    elif isinstance(parsed, dict):
        candidate = (
            parsed.get("items")
            or parsed.get("coverLetters")
            or parsed.get("questions")
            or parsed.get("answers")
            or list(parsed.values())[0]
        )
        # response_format=json_object 사용 시 GPT가 배열을 JSON 문자열로 감싸는 경우 대비
        if isinstance(candidate, str):
            try:
                candidate = json.loads(candidate)
            except Exception:
                raise ValueError(f"GPT 응답 items가 파싱 불가한 문자열입니다: {candidate[:100]}")
        items = candidate
    else:
        raise ValueError("GPT 응답 파싱 실패")

    if not isinstance(items, list):
        raise ValueError(f"GPT 응답 items가 리스트가 아닙니다: {type(items)}")

    # 문항 수 보정 (부족하면 빈 항목 추가)
    existing_q = {item.get("question") for item in items if isinstance(item, dict)}
    for q in questions:
        if q not in existing_q:
            items.append({"question": q, "answer": ""})

    return items


# ─── 메인 함수 ───────────────────────────────────────────────
def generate_cover_letter(
    resume_data: dict,
    company_name: str,
    job_title: str,
    job_description: str = "",
    custom_questions: list[str] | None = None,  # 사용자가 확인/수정한 문항
) -> dict:
    """
    자소서를 재구성합니다.

    Args:
        resume_data:      이력서 데이터
        company_name:     지원 기업명
        job_title:        지원 직무
        job_description:  채용공고 전문 (선택)
        custom_questions: 사용자가 직접 지정한 문항 리스트 (선택)
                          없으면 공고에서 자동 추출 → 실패 시 기본 5문항

    Returns:
        {
            "questions": [...],   # 실제 사용된 문항 리스트
            "source": "custom" | "extracted" | "default",
            "items": [{"question": ..., "answer": ...}, ...]
        }
    """
    # 1. 문항 결정
    if custom_questions and len(custom_questions) > 0:
        questions = custom_questions
        source = "custom"
    else:
        extracted = extract_questions(job_description)
        if extracted:
            questions = extracted
            source = "extracted"
        else:
            questions = DEFAULT_QUESTIONS
            source = "default"

    # 2. 이력서 정보 추출
    resume_summary = build_resume_summary(resume_data)
    base_cover_letter = _extract_base_cover_letter(resume_data)

    # 3. 재구성 생성
    items = _restructure(
        base_cover_letter=base_cover_letter,
        resume_summary=resume_summary,
        company_name=company_name,
        job_title=job_title,
        job_description=job_description,
        questions=questions,
    )

    return {
        "questions": questions,
        "source": source,
        "items": items,
    }
