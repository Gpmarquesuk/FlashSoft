from __future__ import annotations

import io
import os
import wave
from dataclasses import dataclass
from typing import Optional

import requests

from .local_whisper import LocalWhisperClient, LocalWhisperConfig


class WhisperError(Exception):
    """Raised when the OpenRouter Whisper API fails."""


@dataclass
class OpenRouterWhisperClient:
    """
    Thin wrapper around the OpenRouter audio transcription endpoint.
    Tries the remote API first and falls back to a local Whisper model if needed.
    """

    model: str = "openai/whisper-large-v3"
    base_url: str = "https://openrouter.ai/api/v1/audio/transcriptions"
    timeout: float = 45.0
    api_key: Optional[str] = None
    _fallback: Optional[LocalWhisperClient] = None

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise WhisperError("OPENROUTER_API_KEY is not configured.")

    # ------------------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/GpmarquesUK/FlashSoft",
            "X-Title": "flashsoft-interview-assistant",
        }

    def _build_wav_payload(self, audio_bytes: bytes, sample_rate: int) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # int16
            wav.setframerate(sample_rate)
            wav.writeframes(audio_bytes)
        return buffer.getvalue()

    def _call_remote(self, wav_payload: bytes, sample_rate: int) -> str:
        files = {
            "file": ("chunk.wav", wav_payload, "audio/wav"),
        }
        data = {
            "model": self.model,
            "response_format": "text",
            "temperature": 0.0,
            "language": "en",
        }
        response = requests.post(
            self.base_url,
            headers=self._headers(),
            data=data,
            files=files,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise WhisperError(f"OpenRouter Whisper error {response.status_code}: {response.text}")
        return response.text.strip()

    def _ensure_fallback(self) -> LocalWhisperClient:
        if self._fallback is None:
            self._fallback = LocalWhisperClient(
                LocalWhisperConfig(
                    max_history_seconds=12.0,
                    min_window_seconds=3.0,
                    min_increment_seconds=1.2,
                )
            )
        return self._fallback

    # ------------------------------------------------------------------
    def transcribe_chunk(self, audio_bytes: bytes, sample_rate: int) -> str:
        wav_payload = self._build_wav_payload(audio_bytes, sample_rate)
        try:
            return self._call_remote(wav_payload, sample_rate)
        except Exception as exc:
            print(f"[audio] remote whisper failed ({exc}); switching to local fallback.")
            return self._ensure_fallback().transcribe_chunk(audio_bytes, sample_rate)
