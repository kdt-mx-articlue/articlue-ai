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
        lines.append(
            f"""
평가 {index}
- 논리성: {score.logic_score}
- 기술이해도: {score.tech_understanding_score}
- 비즈니스연결성: {score.business_link_score}
- 근거활용도: {score.evidence_score}
- 직무적합도: {score.job_fit_score}
- 총점: {score.total_score}
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

    turn_score = {
        "logicScore": logic_score,
        "techUnderstandingScore": tech_score,
        "businessLinkScore": business_score,
        "evidenceScore": evidence_score,
        "jobFitScore": job_fit_score,
        "totalScore": total_score,
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

    remaining_follow_up_count = max(
        control.max_follow_up_per_question - control.current_follow_up_count,
        0,
    )

    remaining_question_set_count = max(
        control.question_set_count - control.current_question_set_no,
        0,
    )

    user_prompt = FOLLOWUP_USER_PROMPT.format(
        question_set_count=control.question_set_count,
        current_question_set_no=control.current_question_set_no,
        current_follow_up_count=control.current_follow_up_count,
        max_follow_up_per_question=control.max_follow_up_per_question,
        remaining_question_set_count=remaining_question_set_count,
        remaining_follow_up_count=remaining_follow_up_count,
        question_content=current.question_content or "",
        answer_content=current.answer_content or "",
        feedback=turn_score.get("feedback", ""),
    )

    result = llm.invoke_json(
        system_prompt=FOLLOWUP_SYSTEM_PROMPT,
        user_prompt=user_prompt,
    )

    decision = result.get("decision", "NEXT_BASE_QUESTION")

    if remaining_follow_up_count <= 0 and decision == "FOLLOW_UP":
        decision = "NEXT_BASE_QUESTION"

    if remaining_question_set_count <= 0 and decision == "NEXT_BASE_QUESTION":
        decision = "FINISH"

    if decision == "FOLLOW_UP":
        question = {
            "parentQaId": current.interview_qa_id,
            "questionSetNo": control.current_question_set_no,
            "questionType": "FOLLOW_UP",
            "interviewerRole": "기술면접관",
            "questionContent": result.get("followUpQuestion", ""),
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