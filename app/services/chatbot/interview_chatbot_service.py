import logging

from fastapi import UploadFile

from app.api.schemas.interview_graph_schema import (
    InterviewGraphRequest,
    InterviewGraphResponse,
)
from app.graphs.interview_graph import run_interview_graph
from app.services.speech.elevenlabs_speech_service import ElevenLabsSpeechService
from app.services.speech.openai_speech_service import OpenAISpeechService

logger = logging.getLogger(__name__)


class InterviewChatbotService:
    """
    면접 챗봇 서비스.

    역할:
    - LangGraph 기반 면접 한 턴 실행
    - STT 처리 (ElevenLabs → OpenAI Whisper 폴백)
    - TTS 처리 (ElevenLabs → OpenAI TTS 폴백)
    """

    def __init__(self):
        self.elevenlabs = ElevenLabsSpeechService()
        self.openai_speech = OpenAISpeechService()

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
        ElevenLabs STT 우선, 실패 시 OpenAI Whisper 폴백.

        UploadFile은 read() 후 재사용 불가하므로 바이트를 먼저 캐싱한다.
        """
        import io
        from starlette.datastructures import UploadFile as StarletteUploadFile

        audio_bytes = await audio_file.read()
        filename = audio_file.filename or "answer.webm"
        content_type = audio_file.content_type or "audio/webm"

        def make_upload_file() -> UploadFile:
            return StarletteUploadFile(
                filename=filename,
                file=io.BytesIO(audio_bytes),
                headers={"content-type": content_type},
            )

        try:
            return await self.elevenlabs.transcribe(
                audio_file=make_upload_file(),
                language=language,
            )
        except Exception as e:
            logger.warning("ElevenLabs STT 실패, OpenAI Whisper로 폴백합니다. 사유: %s", e)
            return await self.openai_speech.transcribe(
                audio_file=make_upload_file(),
                language=language,
            )

    async def text_to_speech(
        self,
        text: str,
        language: str = "ko",
    ) -> tuple[str, str]:
        """
        챗봇 질문 텍스트를 음성으로 변환한다.
        ElevenLabs TTS 우선, 실패 시 OpenAI TTS 폴백.
        """
        try:
            return await self.elevenlabs.synthesize(
                text=text,
                language=language,
            )
        except Exception as e:
            logger.warning("ElevenLabs TTS 실패, OpenAI TTS로 폴백합니다. 사유: %s", e)
            return await self.openai_speech.synthesize(
                text=text,
                language=language,
            )