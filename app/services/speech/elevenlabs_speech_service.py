import base64
import os
from typing import Any

import httpx
from fastapi import UploadFile


class ElevenLabsSpeechService:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.base_url = os.getenv(
            "ELEVENLABS_BASE_URL",
            "https://api.elevenlabs.io",
        ).rstrip("/")

        self.stt_model_id = os.getenv("ELEVENLABS_STT_MODEL_ID", "scribe_v2")

        self.tts_voice_id = os.getenv("ELEVENLABS_TTS_VOICE_ID")
        self.tts_model_id = os.getenv("ELEVENLABS_TTS_MODEL_ID", "eleven_multilingual_v2")
        self.tts_output_format = os.getenv("ELEVENLABS_TTS_OUTPUT_FORMAT", "mp3_44100_128")

    async def transcribe(
        self,
        audio_file: UploadFile,
        language: str = "ko",
    ) -> str:
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY가 없습니다.")

        audio_bytes = await audio_file.read()

        url = f"{self.base_url}/v1/speech-to-text"

        headers = {
            "xi-api-key": self.api_key,
        }

        files = {
            "file": (
                audio_file.filename or "answer.webm",
                audio_bytes,
                audio_file.content_type or "application/octet-stream",
            )
        }

        data: dict[str, Any] = {
            "model_id": self.stt_model_id,
            "language_code": language,
            "tag_audio_events": "false",
            "diarize": "false",
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                url,
                headers=headers,
                files=files,
                data=data,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"ElevenLabs STT 실패: status={response.status_code}, body={response.text}"
            ) from exc

        body = response.json()
        text = body.get("text")

        if not text:
            raise RuntimeError(f"ElevenLabs STT 응답에 text가 없습니다. body={body}")

        return str(text).strip()

    async def synthesize(
        self,
        text: str,
        language: str = "ko",
    ) -> tuple[str, str]:
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY가 없습니다.")

        if not self.tts_voice_id:
            raise RuntimeError("ELEVENLABS_TTS_VOICE_ID가 없습니다.")

        url = (
            f"{self.base_url}/v1/text-to-speech/"
            f"{self.tts_voice_id}?output_format={self.tts_output_format}"
        )

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        payload = {
            "text": text,
            "model_id": self.tts_model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True,
            },
        }

        async with httpx.AsyncClient(timeout=None) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"ElevenLabs TTS 실패: status={response.status_code}, body={response.text}"
            ) from exc

        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        return audio_base64, "audio/mpeg"