from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.api.schemas.interview_graph_schema import (
    FinalReport,
    InterviewGraphRequest,
    InterviewGraphResponse,
    QuestionResult,
    TurnScore,
)
from app.services.interview.prompt_service import (
    FINAL_REPORT_SYSTEM_PROMPT,
    FINAL_REPORT_USER_PROMPT,
    FOLLOWUP_SYSTEM_PROMPT,
    FOLLOWUP_USER_PROMPT,
    HEADER_SYSTEM_PROMPT,
    HEADER_USER_PROMPT,
    QUESTION_SYSTEM_PROMPT,
    QUESTION_USER_PROMPT,
    SCORING_SYSTEM_PROMPT,
    SCORING_USER_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT,
)
from app.services.interview.score_utils import avg_score, clamp_score
from app.services.llm.llm_json_service import LlmJsonService


ANSWER_STATUS_VALUES = (
    "VALID",
    "PARTIAL",
    "WRONG",
    "EVASIVE",
    "INVALID",
    "ABUSIVE",
)

ANSWER_COMPLETENESS_VALUES = (
    "COMPLETE",
    "SUFFICIENT",
    "PARTIAL",
    "INSUFFICIENT",
    "NONE",
)

FOLLOW_UP_POLICY_VALUES = (
    "NO_FOLLOW_UP",
    "ANCHOR_DEPTH_CHECK",
    "GAP_CHECK",
    "NEXT_TOPIC",
)


class InterviewGraphState(TypedDict, total=False):
    request: InterviewGraphRequest

    route: str
    next_action: str
    reason: str

    document_summary: str
    question_focus_list: list[str]

    question: dict[str, Any] | None
    turn_score: dict[str, Any] | None
    final_report: dict[str, Any] | None

    finish_required: bool


llm = LlmJsonService()


def _to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(by_alias=True)
        except TypeError:
            return value.model_dump()

    if hasattr(value, "dict"):
        try:
            return value.dict(by_alias=True)
        except TypeError:
            return value.dict()

    return {}


def _get_value(source: Any, *names: str, default: Any = None) -> Any:
    if source is None:
        return default

    for name in names:
        if hasattr(source, name):
            value = getattr(source, name)
            if value is not None:
                return value

    source_dict = _to_dict(source)

    for name in names:
        if name in source_dict and source_dict[name] is not None:
            return source_dict[name]

    return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    text = str(value).strip().lower()

    if text in ("true", "1", "yes", "y"):
        return True

    if text in ("false", "0", "no", "n"):
        return False

    return default


def _to_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]

    text = str(value).strip()
    if not text:
        return []

    return [text]


def _normalize_decision(decision: Any) -> str:
    value = str(decision or "NEXT_BASE_QUESTION").strip().upper()

    if value in ("FOLLOW_UP", "ASK_FOLLOW_UP"):
        return "FOLLOW_UP"

    if value in ("NEXT_BASE_QUESTION", "ASK_NEXT_BASE_QUESTION"):
        return "NEXT_BASE_QUESTION"

    if value in ("FINISH", "FINISH_INTERVIEW"):
        return "FINISH"

    return "NEXT_BASE_QUESTION"


def _normalize_answer_status(value: Any) -> str:
    answer_status = str(value or "PARTIAL").strip().upper()

    if answer_status not in ANSWER_STATUS_VALUES:
        return "PARTIAL"

    return answer_status


def _normalize_answer_completeness(value: Any) -> str:
    answer_completeness = str(value or "PARTIAL").strip().upper()

    if answer_completeness not in ANSWER_COMPLETENESS_VALUES:
        return "PARTIAL"

    return answer_completeness


def _normalize_follow_up_policy(value: Any) -> str:
    policy = str(value or "NO_FOLLOW_UP").strip().upper()

    if policy not in FOLLOW_UP_POLICY_VALUES:
        return "NO_FOLLOW_UP"

    return policy


def _looks_evasive_or_no_experience(answer_content: str) -> bool:
    text = (answer_content or "").strip()
    compact = text.replace(" ", "").replace("\n", "").lower()

    if not compact:
        return True

    evasive_patterns = (
        "잘모르",
        "모르겠",
        "잘모름",
        "기억나지",
        "생각나지",
        "해본적없",
        "구현해본적없",
        "직접구현해본적없",
        "경험이없",
        "사례는없",
        "딱히없",
        "왜자꾸",
        "답변하기어렵",
    )

    return any(pattern in compact for pattern in evasive_patterns)


def _should_finish_or_next_base(
    *,
    remaining_question_set_count: int,
    reason: str,
) -> InterviewGraphState:
    if remaining_question_set_count <= 0:
        return {
            "next_action": "FINISH_INTERVIEW",
            "question": None,
            "finish_required": True,
            "reason": reason + " 남은 기본 질문 세트가 없어 면접 종료로 전환했습니다.",
        }

    return {
        "next_action": "ASK_NEXT_BASE_QUESTION",
        "question": None,
        "finish_required": False,
        "reason": reason + " 다음 기본 질문으로 전환했습니다.",
    }


def _format_qas(request: InterviewGraphRequest) -> str:
    qas = request.history.previous_qas

    if not qas:
        return "이전 질문/답변 없음"

    lines = []

    for qa in qas:
        lines.append(
            f"""
질문순번: {qa.question_order}
질문세트번호: {qa.question_set_no}
질문유형: {qa.question_type}
면접관역할: {qa.interviewer_role}
꼬리질문여부: {qa.follow_up_yn}
질문: {qa.question_content}
답변: {qa.answer_content or "미답변"}
""".strip()
        )

    return "\n\n".join(lines)


def _format_scores(request: InterviewGraphRequest) -> str:
    scores = request.history.previous_scores

    if not scores:
        return "누적 점수 없음"

    lines = []

    for index, score in enumerate(scores, start=1):
        answer_status = _get_value(score, "answer_status", "answerStatus", default=None)
        answer_completeness = _get_value(score, "answer_completeness", "answerCompleteness", default=None)
        follow_up_policy = _get_value(score, "follow_up_policy", "followUpPolicy", default=None)
        follow_up_worthiness = _get_value(score, "follow_up_worthiness", "followUpWorthiness", default=None)
        risk_flags = _get_value(score, "risk_flags", "riskFlags", default=None)

        extra_lines = []
        if answer_status:
            extra_lines.append(f"- 답변상태: {answer_status}")
        if answer_completeness:
            extra_lines.append(f"- 답변완성도: {answer_completeness}")
        if follow_up_policy:
            extra_lines.append(f"- 꼬리질문정책: {follow_up_policy}")
        if follow_up_worthiness is not None:
            extra_lines.append(f"- 꼬리질문가치: {follow_up_worthiness}")
        if risk_flags:
            extra_lines.append(f"- 위험플래그: {risk_flags}")

        extra_text = "\n" + "\n".join(extra_lines) if extra_lines else ""

        lines.append(
            f"""
평가 {index}
- 논리성: {score.logic_score}
- 기술이해도: {score.tech_understanding_score}
- 비즈니스연결성: {score.business_link_score}
- 근거활용도: {score.evidence_score}
- 직무적합도: {score.job_fit_score}
- 총점: {score.total_score}{extra_text}
- 피드백: {score.feedback}
""".strip()
        )

    return "\n\n".join(lines)


def header_node(state: InterviewGraphState) -> InterviewGraphState:
    request = state["request"]
    session = request.session
    control = request.control

    user_prompt = HEADER_USER_PROMPT.format(
        event_type=request.event_type,
        target_company=session.target_company,
        job_posting_title=session.job_posting_title,
        interview_type=session.interview_type,
        interview_level=session.interview_level,
        interview_format=session.interview_format,
        interviewer_style=session.interviewer_style,
        chat_mode=session.chat_mode,
        question_set_count=control.question_set_count,
        current_question_set_no=control.current_question_set_no,
        current_follow_up_count=control.current_follow_up_count,
        max_follow_up_per_question=control.max_follow_up_per_question,
        total_question_count=control.total_question_count,
        total_answer_count=control.total_answer_count,
    )

    result = llm.invoke_json(
        system_prompt=HEADER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    if request.event_type == "START":
        route = "summary"
        next_action = "ASK_FIRST_QUESTION"
    elif request.event_type == "ANSWER":
        route = "score"
        next_action = "SCORE_AND_DECIDE"
    else:
        route = "final_report"
        next_action = "FINISH_INTERVIEW"

    return {
        "route": route,
        "next_action": next_action,
        "reason": result.get("reason", ""),
    }


def route_after_header(state: InterviewGraphState) -> str:
    return state.get("route", "summary")


def summary_node(state: InterviewGraphState) -> InterviewGraphState:
    request = state["request"]
    context = request.context

    user_prompt = SUMMARY_USER_PROMPT.format(
        resume_text=context.resume_text,
        job_posting_text=context.job_posting_text,
        portfolio_text=context.portfolio_text,
    )

    result = llm.invoke_json(
        system_prompt=SUMMARY_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    return {
        "document_summary": result.get("documentSummary", ""),
        "question_focus_list": result.get("questionFocusList", []),
    }


def question_generator_node(state: InterviewGraphState) -> InterviewGraphState:
    request = state["request"]
    session = request.session
    control = request.control

    document_summary = state.get("document_summary")
    if not document_summary:
        document_summary = "문서 요약은 별도로 생성되지 않았습니다. 제공된 문맥과 이전 질문/답변을 기준으로 질문하세요."

    if request.event_type == "START":
        next_question_set_no = 1
        next_action = "ASK_FIRST_QUESTION"
    else:
        next_question_set_no = control.current_question_set_no + 1
        next_action = "ASK_NEXT_BASE_QUESTION"

    user_prompt = QUESTION_USER_PROMPT.format(
        target_company=session.target_company,
        job_posting_title=session.job_posting_title,
        interview_type=session.interview_type,
        interview_level=session.interview_level,
        interviewer_style=session.interviewer_style,
        next_question_set_no=next_question_set_no,
        document_summary=document_summary,
        question_focus_list=state.get("question_focus_list", []),
        previous_qas=_format_qas(request),
    )

    result = llm.invoke_json(
        system_prompt=QUESTION_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    question = {
        "parentQaId": None,
        "questionSetNo": next_question_set_no,
        "questionType": result.get("questionType", "TECH"),
        "interviewerRole": result.get("interviewerRole", "기술면접관"),
        "questionContent": result.get("questionContent", ""),
        "followUpYn": "N",
    }

    return {
        "next_action": next_action,
        "question": question,
        "finish_required": False,
    }


def score_node(state: InterviewGraphState) -> InterviewGraphState:
    request = state["request"]
    session = request.session
    current = request.current_turn

    if current is None:
        return {
            "turn_score": None,
            "reason": "currentTurn이 없어 점수화를 생략했습니다.",
        }

    user_prompt = SCORING_USER_PROMPT.format(
        target_company=session.target_company,
        job_posting_title=session.job_posting_title,
        interview_type=session.interview_type,
        interviewer_style=session.interviewer_style,
        document_summary=state.get("document_summary", ""),
        question_type=current.question_type or "UNKNOWN",
        question_content=current.question_content or "",
        answer_content=current.answer_content or "",
    )

    result = llm.invoke_json(
        system_prompt=SCORING_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    logic_score = clamp_score(result.get("logicScore"))
    tech_score = clamp_score(result.get("techUnderstandingScore"))
    business_score = clamp_score(result.get("businessLinkScore"))
    evidence_score = clamp_score(result.get("evidenceScore"))
    job_fit_score = clamp_score(result.get("jobFitScore"))

    total_score = clamp_score(result.get("totalScore"))
    if total_score <= 0:
        total_score = avg_score(
            logic_score,
            tech_score,
            business_score,
            evidence_score,
            job_fit_score,
        )

    answer_status = _normalize_answer_status(result.get("answerStatus"))
    answer_completeness = _normalize_answer_completeness(result.get("answerCompleteness"))
    follow_up_policy = _normalize_follow_up_policy(result.get("followUpPolicy"))

    technical_anchors = _to_list(result.get("technicalAnchors"))
    missing_core_points = _to_list(result.get("missingCorePoints"))
    risk_flags = _to_list(result.get("riskFlags"))

    has_technical_anchor = _to_bool(
        result.get("hasTechnicalAnchor"),
        default=bool(technical_anchors),
    )

    intent_matched = _to_bool(result.get("intentMatched"), default=True)
    should_ask_follow_up = _to_bool(result.get("shouldAskFollowUp"), default=False)
    follow_up_worthiness = clamp_score(result.get("followUpWorthiness"))
    recommended_follow_up_focus = str(result.get("recommendedFollowUpFocus", "") or "").strip()

    current_answer = current.answer_content or ""

    # LLM이 놓쳐도 서버에서 회피성 답변은 강제로 보정한다.
    if _looks_evasive_or_no_experience(current_answer):
        answer_status = "EVASIVE"
        answer_completeness = "NONE"
        should_ask_follow_up = False
        follow_up_policy = "NEXT_TOPIC"
        follow_up_worthiness = 0
        recommended_follow_up_focus = ""
        if "EVASIVE" not in risk_flags:
            risk_flags.append("EVASIVE")

    # 꼬리질문이 필요하다고 했지만 기술 앵커나 초점이 없으면 서버에서 차단한다.
    if should_ask_follow_up and (not has_technical_anchor or not recommended_follow_up_focus):
        should_ask_follow_up = False
        follow_up_policy = "NEXT_TOPIC"
        follow_up_worthiness = min(follow_up_worthiness, 40)

    turn_score = {
        "logicScore": logic_score,
        "techUnderstandingScore": tech_score,
        "businessLinkScore": business_score,
        "evidenceScore": evidence_score,
        "jobFitScore": job_fit_score,
        "totalScore": total_score,

        "answerStatus": answer_status,
        "intentMatched": intent_matched,
        "answerCompleteness": answer_completeness,

        "hasTechnicalAnchor": has_technical_anchor,
        "technicalAnchors": technical_anchors,
        "missingCorePoints": missing_core_points,
        "riskFlags": risk_flags,

        "followUpPolicy": follow_up_policy,
        "followUpWorthiness": follow_up_worthiness,
        "shouldAskFollowUp": should_ask_follow_up,
        "recommendedFollowUpFocus": recommended_follow_up_focus,

        "feedback": result.get("feedback", ""),
    }

    return {
        "turn_score": turn_score,
    }


def followup_judge_node(state: InterviewGraphState) -> InterviewGraphState:
    request = state["request"]
    control = request.control
    current = request.current_turn
    turn_score = state.get("turn_score") or {}

    if current is None:
        return {
            "next_action": "FINISH_INTERVIEW",
            "finish_required": True,
            "reason": "currentTurn이 없어 면접 종료로 판단했습니다.",
        }

    question_set_count = _to_int(
        _get_value(control, "question_set_count", "questionSetCount", default=0),
        0,
    )

    current_question_set_no = _to_int(
        _get_value(control, "current_question_set_no", "currentQuestionSetNo", default=0),
        0,
    )

    current_follow_up_count = _to_int(
        _get_value(control, "current_follow_up_count", "currentFollowUpCount", default=0),
        0,
    )

    max_follow_up_per_question = _to_int(
        _get_value(control, "max_follow_up_per_question", "maxFollowUpPerQuestion", default=0),
        0,
    )

    computed_remaining_follow_up_count = max(
        max_follow_up_per_question - current_follow_up_count,
        0,
    )

    computed_remaining_question_set_count = max(
        question_set_count - current_question_set_no,
        0,
    )

    remaining_follow_up_count = _to_int(
        _get_value(
            control,
            "remaining_follow_up_count",
            "remainingFollowUpCount",
            default=computed_remaining_follow_up_count,
        ),
        computed_remaining_follow_up_count,
    )

    remaining_question_set_count = _to_int(
        _get_value(
            control,
            "remaining_question_set_count",
            "remainingQuestionSetCount",
            default=computed_remaining_question_set_count,
        ),
        computed_remaining_question_set_count,
    )

    force_next_action = str(
        _get_value(
            control,
            "force_next_action",
            "forceNextAction",
            default="",
        ) or ""
    ).strip().upper()

    follow_up_allowed = _to_bool(
        _get_value(
            control,
            "follow_up_allowed",
            "followUpAllowed",
            default=remaining_follow_up_count > 0,
        ),
        default=remaining_follow_up_count > 0,
    )

    logic_score = clamp_score(turn_score.get("logicScore"))
    tech_score = clamp_score(turn_score.get("techUnderstandingScore"))
    business_score = clamp_score(turn_score.get("businessLinkScore"))
    evidence_score = clamp_score(turn_score.get("evidenceScore"))
    job_fit_score = clamp_score(turn_score.get("jobFitScore"))

    total_score = clamp_score(turn_score.get("totalScore"))
    if total_score <= 0:
        total_score = avg_score(
            logic_score,
            tech_score,
            business_score,
            evidence_score,
            job_fit_score,
        )

    answer_status = _normalize_answer_status(turn_score.get("answerStatus"))
    answer_completeness = _normalize_answer_completeness(turn_score.get("answerCompleteness"))
    follow_up_policy = _normalize_follow_up_policy(turn_score.get("followUpPolicy"))

    intent_matched = _to_bool(turn_score.get("intentMatched"), default=True)
    has_technical_anchor = _to_bool(turn_score.get("hasTechnicalAnchor"), default=False)
    technical_anchors = _to_list(turn_score.get("technicalAnchors"))
    missing_core_points = _to_list(turn_score.get("missingCorePoints"))
    risk_flags = _to_list(turn_score.get("riskFlags"))

    should_ask_follow_up = _to_bool(turn_score.get("shouldAskFollowUp"), default=False)
    follow_up_worthiness = clamp_score(turn_score.get("followUpWorthiness"))
    recommended_follow_up_focus = str(turn_score.get("recommendedFollowUpFocus", "") or "").strip()

    feedback = turn_score.get("feedback", "")
    current_answer = current.answer_content or ""

    if force_next_action == "NEXT_BASE_QUESTION":
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="Node 제어값 forceNextAction에 따라",
        )

    if (
        not follow_up_allowed
        or remaining_follow_up_count <= 0
        or current_follow_up_count >= max_follow_up_per_question
    ):
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="꼬리질문 제한에 도달했거나 허용되지 않아",
        )

    # 회피성/무경험 답변은 점수만 낮게 주고 더 캐묻지 않는다.
    if _looks_evasive_or_no_experience(current_answer):
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="답변이 회피성 또는 경험 부재 답변으로 판단되어 꼬리질문 없이",
        )

    if answer_status in ("WRONG", "EVASIVE", "INVALID", "ABUSIVE"):
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason=f"답변 상태가 {answer_status}이므로 꼬리질문 없이",
        )

    if not should_ask_follow_up:
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="분석 결과 shouldAskFollowUp이 false이므로",
        )

    if follow_up_policy not in ("ANCHOR_DEPTH_CHECK", "GAP_CHECK"):
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason=f"꼬리질문 정책이 {follow_up_policy}이므로",
        )

    if not has_technical_anchor or not technical_anchors:
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="검증할 기술 앵커가 없어",
        )

    if not recommended_follow_up_focus:
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="권장 꼬리질문 초점이 없어",
        )

    # 충분한 답변은 원칙적으로 다음 기본 질문.
    # 단, 실제 사용 여부를 검증할 가치가 매우 높은 기술 앵커가 있을 때만 1회 허용.
    if answer_status == "VALID":
        if (
            follow_up_policy != "ANCHOR_DEPTH_CHECK"
            or follow_up_worthiness < 85
            or current_follow_up_count > 0
        ):
            return _should_finish_or_next_base(
                remaining_question_set_count=remaining_question_set_count,
                reason="답변 상태가 VALID이고 추가 깊이 검증 조건을 충족하지 않아",
            )

    # PARTIAL 답변도 단순 누락이면 꼬리질문하지 않는다.
    if answer_status == "PARTIAL":
        if follow_up_worthiness < 65:
            return _should_finish_or_next_base(
                remaining_question_set_count=remaining_question_set_count,
                reason="PARTIAL 답변이지만 꼬리질문 가치가 낮아",
            )

    if total_score >= 75 and follow_up_worthiness < 85:
        return _should_finish_or_next_base(
            remaining_question_set_count=remaining_question_set_count,
            reason="총점이 충분하고 꼬리질문 가치가 매우 높지 않아",
        )

    user_prompt = FOLLOWUP_USER_PROMPT.format(
        force_next_action=force_next_action,
        follow_up_allowed=str(follow_up_allowed).lower(),

        question_set_count=question_set_count,
        current_question_set_no=current_question_set_no,
        current_follow_up_count=current_follow_up_count,
        max_follow_up_per_question=max_follow_up_per_question,
        remaining_question_set_count=remaining_question_set_count,
        remaining_follow_up_count=remaining_follow_up_count,

        question_content=current.question_content or "",
        answer_content=current.answer_content or "",

        logic_score=logic_score,
        tech_understanding_score=tech_score,
        business_link_score=business_score,
        evidence_score=evidence_score,
        job_fit_score=job_fit_score,
        total_score=total_score,

        answer_status=answer_status,
        intent_matched=str(intent_matched).lower(),
        answer_completeness=answer_completeness,
        has_technical_anchor=str(has_technical_anchor).lower(),
        technical_anchors=technical_anchors,
        missing_core_points=missing_core_points,
        risk_flags=risk_flags,
        follow_up_policy=follow_up_policy,
        follow_up_worthiness=follow_up_worthiness,
        should_ask_follow_up=str(should_ask_follow_up).lower(),
        recommended_follow_up_focus=recommended_follow_up_focus,

        feedback=feedback,
        previous_qas=_format_qas(request),
    )

    result = llm.invoke_json(
        system_prompt=FOLLOWUP_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    decision = _normalize_decision(result.get("decision", "NEXT_BASE_QUESTION"))

    if decision == "FOLLOW_UP":
        if (
            not follow_up_allowed
            or remaining_follow_up_count <= 0
            or current_follow_up_count >= max_follow_up_per_question
            or answer_status in ("WRONG", "EVASIVE", "INVALID", "ABUSIVE")
            or not should_ask_follow_up
            or follow_up_policy not in ("ANCHOR_DEPTH_CHECK", "GAP_CHECK")
            or not has_technical_anchor
            or not recommended_follow_up_focus
        ):
            decision = "NEXT_BASE_QUESTION"

        if answer_status == "VALID" and (
            follow_up_policy != "ANCHOR_DEPTH_CHECK"
            or follow_up_worthiness < 85
            or current_follow_up_count > 0
        ):
            decision = "NEXT_BASE_QUESTION"

        if answer_status == "PARTIAL" and follow_up_worthiness < 65:
            decision = "NEXT_BASE_QUESTION"

    if decision == "NEXT_BASE_QUESTION" and remaining_question_set_count <= 0:
        decision = "FINISH"

    if decision == "FOLLOW_UP":
        follow_up_question = str(result.get("followUpQuestion", "") or "").strip()

        if not follow_up_question:
            return _should_finish_or_next_base(
                remaining_question_set_count=remaining_question_set_count,
                reason="FOLLOW_UP 결정이 있었지만 꼬리질문 본문이 없어",
            )

        question = {
            "parentQaId": current.interview_qa_id,
            "questionSetNo": current_question_set_no,
            "questionType": "FOLLOW_UP",
            "interviewerRole": "기술면접관",
            "questionContent": follow_up_question,
            "followUpYn": "Y",
        }

        return {
            "next_action": "ASK_FOLLOW_UP",
            "question": question,
            "finish_required": False,
            "reason": result.get("reason", ""),
        }

    if decision == "FINISH":
        return {
            "next_action": "FINISH_INTERVIEW",
            "question": None,
            "finish_required": True,
            "reason": result.get("reason", ""),
        }

    return {
        "next_action": "ASK_NEXT_BASE_QUESTION",
        "question": None,
        "finish_required": False,
        "reason": result.get("reason", ""),
    }


def route_after_followup_judge(state: InterviewGraphState) -> str:
    next_action = state.get("next_action")

    if next_action == "ASK_NEXT_BASE_QUESTION":
        return "question_generator"

    return END


def final_report_node(state: InterviewGraphState) -> InterviewGraphState:
    request = state["request"]
    session = request.session

    user_prompt = FINAL_REPORT_USER_PROMPT.format(
        target_company=session.target_company,
        job_posting_title=session.job_posting_title,
        interview_type=session.interview_type,
        interviewer_style=session.interviewer_style,
        previous_qas=_format_qas(request),
        previous_scores=_format_scores(request),
    )

    result = llm.invoke_json(
        system_prompt=FINAL_REPORT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    logic_score = clamp_score(result.get("logicScore"))
    tech_score = clamp_score(result.get("techUnderstandingScore"))
    business_score = clamp_score(result.get("businessLinkScore"))
    evidence_score = clamp_score(result.get("evidenceScore"))
    job_fit_score = clamp_score(result.get("jobFitScore"))

    total_score = clamp_score(result.get("totalScore"))
    if total_score <= 0:
        total_score = avg_score(
            logic_score,
            tech_score,
            business_score,
            evidence_score,
            job_fit_score,
        )

    final_report = {
        "logicScore": logic_score,
        "techUnderstandingScore": tech_score,
        "businessLinkScore": business_score,
        "evidenceScore": evidence_score,
        "jobFitScore": job_fit_score,
        "totalScore": total_score,
        "summary": result.get("summary", ""),
        "reportItems": result.get("reportItems", []),
    }

    return {
        "next_action": "FINISH_INTERVIEW",
        "final_report": final_report,
        "finish_required": True,
    }


def build_graph():
    graph = StateGraph(InterviewGraphState)

    graph.add_node("header", header_node)
    graph.add_node("summary", summary_node)
    graph.add_node("question_generator", question_generator_node)
    graph.add_node("score", score_node)
    graph.add_node("followup_judge", followup_judge_node)
    graph.add_node("final_report", final_report_node)

    graph.add_edge(START, "header")

    graph.add_conditional_edges(
        "header",
        route_after_header,
        {
            "summary": "summary",
            "score": "score",
            "final_report": "final_report",
        },
    )

    graph.add_edge("summary", "question_generator")
    graph.add_edge("question_generator", END)

    graph.add_edge("score", "followup_judge")

    graph.add_conditional_edges(
        "followup_judge",
        route_after_followup_judge,
        {
            "question_generator": "question_generator",
            END: END,
        },
    )

    graph.add_edge("final_report", END)

    return graph.compile()


compiled_graph = build_graph()


def run_interview_graph(request: InterviewGraphRequest) -> InterviewGraphResponse:
    result = compiled_graph.invoke({
        "request": request,
    })

    question = result.get("question")
    turn_score = result.get("turn_score")
    final_report = result.get("final_report")

    return InterviewGraphResponse(
        nextAction=result.get("next_action", "ERROR"),
        question=QuestionResult(**question) if question else None,
        turnScore=TurnScore(**turn_score) if turn_score else None,
        finalReport=FinalReport(**final_report) if final_report else None,
        finishRequired=bool(result.get("finish_required", False)),
        reason=result.get("reason"),
    )