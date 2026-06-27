from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


EventType = Literal["START", "ANSWER", "FINISH"]

NextAction = Literal[
    "ASK_FIRST_QUESTION",
    "ASK_NEXT_BASE_QUESTION",
    "ASK_FOLLOW_UP",
    "FINISH_INTERVIEW",
    "ERROR",
]

ChatMode = Literal["TEXT", "VOICE"]
InterviewType = Literal["GENERAL", "PRESSURE"]
InterviewLevel = Literal["NORMAL"]
InterviewFormat = Literal["ONE_TO_ONE"]
InterviewerStyle = Literal[
    "NORMAL",
    "CALM",
    "SHARP",
    "FRIENDLY",
    "PRACTICAL",
]


class BaseCamelModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )


class SessionState(BaseCamelModel):
    interview_session_id: Optional[int] = Field(default=None, alias="interviewSessionId")
    resume_id: int = Field(alias="resumeId")
    job_posting_id: int = Field(alias="jobPostingId")

    target_company: Optional[str] = Field(default=None, alias="targetCompany")
    job_posting_title: Optional[str] = Field(default=None, alias="jobPostingTitle")

    interview_type: InterviewType = Field(alias="interviewType")
    interview_level: InterviewLevel = Field(default="NORMAL", alias="interviewLevel")
    interview_format: InterviewFormat = Field(default="ONE_TO_ONE", alias="interviewFormat")

    interviewer_style: InterviewerStyle = Field(default="NORMAL", alias="interviewerStyle")
    chat_mode: ChatMode = Field(default="TEXT", alias="chatMode")


class ControlState(BaseCamelModel):
    question_set_count: int = Field(alias="questionSetCount")
    max_follow_up_per_question: int = Field(default=3, alias="maxFollowUpPerQuestion")

    current_question_set_no: int = Field(default=0, alias="currentQuestionSetNo")
    current_base_question_id: Optional[int] = Field(default=None, alias="currentBaseQuestionId")
    current_follow_up_count: int = Field(default=0, alias="currentFollowUpCount")

    remaining_question_set_count: int = Field(default=0, alias="remainingQuestionSetCount")
    remaining_follow_up_count: int = Field(default=0, alias="remainingFollowUpCount")

    total_question_count: int = Field(default=0, alias="totalQuestionCount")
    total_answer_count: int = Field(default=0, alias="totalAnswerCount")

    follow_up_allowed: bool = Field(default=True, alias="followUpAllowed")
    force_next_action: Optional[str] = Field(default=None, alias="forceNextAction")
    guard_reason: Optional[str] = Field(default=None, alias="guardReason")


class InterviewContext(BaseCamelModel):
    resume_text: str = Field(default="", alias="resumeText")
    job_posting_text: str = Field(default="", alias="jobPostingText")
    portfolio_text: str = Field(default="", alias="portfolioText")
    weak_points_text: str = Field(default="", alias="weakPointsText")


class QaItem(BaseCamelModel):
    interview_qa_id: Optional[int] = Field(default=None, alias="interviewQaId")
    parent_qa_id: Optional[int] = Field(default=None, alias="parentQaId")

    question_set_no: Optional[int] = Field(default=None, alias="questionSetNo")
    question_order: int = Field(alias="questionOrder")

    question_type: str = Field(alias="questionType")
    interviewer_role: Optional[str] = Field(default=None, alias="interviewerRole")

    question_content: str = Field(alias="questionContent")
    answer_content: Optional[str] = Field(default=None, alias="answerContent")

    follow_up_yn: str = Field(default="N", alias="followUpYn")


class TurnScore(BaseCamelModel):
    logic_score: float = Field(alias="logicScore")
    tech_understanding_score: float = Field(alias="techUnderstandingScore")
    business_link_score: float = Field(alias="businessLinkScore")
    evidence_score: float = Field(alias="evidenceScore")
    job_fit_score: float = Field(alias="jobFitScore")
    total_score: float = Field(alias="totalScore")

    answer_status: Optional[str] = Field(default=None, alias="answerStatus")
    intent_matched: Optional[bool] = Field(default=None, alias="intentMatched")
    answer_completeness: Optional[str] = Field(default=None, alias="answerCompleteness")

    has_technical_anchor: Optional[bool] = Field(default=None, alias="hasTechnicalAnchor")
    technical_anchors: list[str] = Field(default_factory=list, alias="technicalAnchors")
    missing_core_points: list[str] = Field(default_factory=list, alias="missingCorePoints")
    risk_flags: list[str] = Field(default_factory=list, alias="riskFlags")

    follow_up_policy: Optional[str] = Field(default=None, alias="followUpPolicy")
    follow_up_worthiness: Optional[float] = Field(default=None, alias="followUpWorthiness")
    should_ask_follow_up: Optional[bool] = Field(default=None, alias="shouldAskFollowUp")
    recommended_follow_up_focus: Optional[str] = Field(default=None, alias="recommendedFollowUpFocus")

    feedback: str


class CurrentTurn(BaseCamelModel):
    interview_qa_id: Optional[int] = Field(default=None, alias="interviewQaId")
    parent_qa_id: Optional[int] = Field(default=None, alias="parentQaId")
    question_content: Optional[str] = Field(default=None, alias="questionContent")
    answer_content: Optional[str] = Field(default=None, alias="answerContent")
    question_type: Optional[str] = Field(default=None, alias="questionType")
    follow_up_yn: Optional[str] = Field(default=None, alias="followUpYn")


class HistoryState(BaseCamelModel):
    previous_qas: list[QaItem] = Field(default_factory=list, alias="previousQas")
    previous_scores: list[TurnScore] = Field(default_factory=list, alias="previousScores")


class InterviewGraphRequest(BaseCamelModel):
    event_type: EventType = Field(alias="eventType")
    session: SessionState
    control: ControlState
    context: InterviewContext
    history: HistoryState = Field(default_factory=HistoryState)
    current_turn: Optional[CurrentTurn] = Field(default=None, alias="currentTurn")


class QuestionResult(BaseCamelModel):
    parent_qa_id: Optional[int] = Field(default=None, alias="parentQaId")
    question_set_no: Optional[int] = Field(default=None, alias="questionSetNo")
    question_type: str = Field(alias="questionType")
    interviewer_role: str = Field(alias="interviewerRole")
    question_content: str = Field(alias="questionContent")
    follow_up_yn: str = Field(alias="followUpYn")


class FinalReportItem(BaseCamelModel):
    feedback_type: str = Field(alias="feedbackType")
    feedback_content: str = Field(alias="feedbackContent")
    display_order: int = Field(alias="displayOrder")


class FinalReport(BaseCamelModel):
    logic_score: float = Field(alias="logicScore")
    tech_understanding_score: float = Field(alias="techUnderstandingScore")
    business_link_score: float = Field(alias="businessLinkScore")
    evidence_score: float = Field(alias="evidenceScore")
    job_fit_score: float = Field(alias="jobFitScore")
    total_score: float = Field(alias="totalScore")
    summary: str
    report_items: list[FinalReportItem] = Field(alias="reportItems")


class InterviewGraphResponse(BaseCamelModel):
    next_action: NextAction = Field(alias="nextAction")
    question: Optional[QuestionResult] = None
    turn_score: Optional[TurnScore] = Field(default=None, alias="turnScore")
    final_report: Optional[FinalReport] = Field(default=None, alias="finalReport")
    finish_required: bool = Field(default=False, alias="finishRequired")
    reason: Optional[str] = None


class SttResponse(BaseCamelModel):
    text: str


class TtsRequest(BaseCamelModel):
    text: str
    language: str = "ko"


class TtsResponse(BaseCamelModel):
    audio_base64: str = Field(alias="audioBase64")
    mime_type: str = Field(alias="mimeType")