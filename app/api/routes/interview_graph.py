from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.schemas.interview_graph_schema import (
    InterviewGraphRequest,
    InterviewGraphResponse,
    SttResponse,
    TtsRequest,
    TtsResponse,
)
from app.services.chatbot.interview_chatbot_service import InterviewChatbotService
from app.utils.json_utils import JsonParseError


router = APIRouter(
    prefix="/api/interview-graph",
    tags=["Interview Chatbot"],
)

chatbot_service = InterviewChatbotService()


@router.post("/run", response_model=InterviewGraphResponse)
async def run_chatbot_turn(request: InterviewGraphRequest):
    try:
        return chatbot_service.run_chatbot_turn(request)

    except JsonParseError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"LLM JSON 파싱 실패: {str(exc)}",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"면접 챗봇 실행 실패: {str(exc)}",
        )


@router.post("/stt", response_model=SttResponse)
async def speech_to_text(
    audioFile: UploadFile = File(...),
    language: str = Form(default="ko"),
):
    try:
        text = await chatbot_service.speech_to_text(
            audio_file=audioFile,
            language=language,
        )

        return SttResponse(text=text)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"STT 처리 실패: {str(exc)}",
        )


@router.post("/tts", response_model=TtsResponse)
async def text_to_speech(request: TtsRequest):
    try:
        audio_base64, mime_type = await chatbot_service.text_to_speech(
            text=request.text,
            language=request.language,
        )

        return TtsResponse(
            audioBase64=audio_base64,
            mimeType=mime_type,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"TTS 처리 실패: {str(exc)}",
        )