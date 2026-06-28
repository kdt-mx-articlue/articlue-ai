import base64
import io

from fastapi import UploadFile
from openai import AsyncOpenAI

client = AsyncOpenAI()


class OpenAISpeechService:
    """
    OpenAI TTS(tts-1) + Whisper(whisper-1) 기반 음성 서비스.
    ElevenLabs 실패 시 폴백으로 사용된다.
    """

    TTS_MODEL = "tts-1"
    TTS_VOICE = "alloy"   # alloy | echo | fable | onyx | nova | shimmer
    STT_MODEL = "whisper-1"

    async def synthesize(
        self,
        text: str,
        language: str = "ko",
    ) -> tuple[str, str]:
        """
        텍스트 → 음성 (mp3 base64 반환)
        """
        response = await client.audio.speech.create(
            model=self.TTS_MODEL,
            voice=self.TTS_VOICE,
            input=text,
            response_format="mp3",
        )
        audio_bytes = response.read()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return audio_base64, "audio/mpeg"

    async def transcribe(
        self,
        audio_file: UploadFile,
        language: str = "ko",
    ) -> str:
        """
        음성 → 텍스트 (Whisper)
        """
        audio_bytes = await audio_file.read()
        filename = audio_file.filename or "answer.webm"

        transcription = await client.audio.transcriptions.create(
            model=self.STT_MODEL,
            file=(filename, io.BytesIO(audio_bytes), audio_file.content_type or "audio/webm"),
            language=language,
        )
        return transcription.text.strip()
