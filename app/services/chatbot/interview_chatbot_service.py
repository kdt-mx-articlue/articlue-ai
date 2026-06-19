from fastapi import UploadFile

from app.api.schemas.interview_graph_schema import (
    InterviewGraphRequest,
    InterviewGraphResponse,
)
from app.graphs.interview_graph import run_interview_graph
from app.services.speech.elevenlabs_speech_service import ElevenLabsSpeechService


class InterviewChatbotService:
    """
    면접 챗봇 서비스.

    역할:
    - LangGraph 기반 면접 한 턴 실행
    - STT 처리
    - TTS 처리

    routes에서 LangGraph와 ElevenLabs를 직접 호출하지 않고,
    이 서비스 계층을 통해 호출하도록 분리한다.
    """

    def __init__(self):
        self.speech_service = ElevenLabsSpeechService()

    def run_chatbot_turn(
        self,
        request: InterviewGraphRequest,
    ) -> InterviewGraphResponse:
        """
        면접 챗봇 한 턴 실행.

        eventType:
        - START  : 첫 질문 생성
        - ANSWER : 답변 평가 후 꼬리질문/다음 기본질문/종료 판단
        - FINISH : 최종 리포트 생성
        """

        return run_interview_graph(request)

    async def speech_to_text(
        self,
        audio_file: UploadFile,
        language: str = "ko",
    ) -> str:
        """
        음성 답변을 텍스트로 변환한다.
        """

        return await self.speech_service.transcribe(
            audio_file=audio_file,
            language=language,
        )

    async def text_to_speech(
        self,
        text: str,
        language: str = "ko",
    ) -> tuple[str, str]:
        """
        챗봇 질문 텍스트를 음성으로 변환한다.
        """

        return await self.speech_service.synthesize(
            text=text,
            language=language,
        )