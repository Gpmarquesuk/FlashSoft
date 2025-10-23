from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    from faster_whisper import WhisperModel
except ImportError as exc:  # pragma: no cover - dependency missing
    raise RuntimeError(
        "O pacote 'faster-whisper' é necessário para a transcrição local. "
        "Instale com 'pip install faster-whisper'."
    ) from exc


def _detect_device() -> str:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


@dataclass
class LocalWhisperConfig:
    model_size: str = "base"
    language: str = "en"
    compute_type: str = "int8"
    max_history_seconds: float = 12.0
    min_window_seconds: float = 3.0
    min_increment_seconds: float = 1.2


class LocalWhisperClient:
    """
    Transcrição incremental baseada em Faster-Whisper.

    Mantém um buffer deslizante dos últimos `max_history_seconds` e retorna apenas
    o texto novo produzido em relação ao chunk anterior.
    """

    def __init__(self, config: Optional[LocalWhisperConfig] = None) -> None:
        self.config = config or LocalWhisperConfig()
        device = _detect_device()
        compute_type = self.config.compute_type
        if device == "cuda" and compute_type == "int8":
            compute_type = "float16"

        self._model = WhisperModel(
            self.config.model_size,
            device=device,
            compute_type=compute_type,
            cpu_threads=2,
        )
        self._buffer = np.zeros(0, dtype=np.float32)
        self._sample_rate: Optional[int] = None
        self._last_segment_end = 0.0
        self._lock = threading.Lock()

    def reset(self) -> None:
        with self._lock:
            self._buffer = np.zeros(0, dtype=np.float32)
            self._sample_rate = None
            self._last_segment_end = 0.0

    def transcribe_chunk(self, audio_bytes: bytes, sample_rate: int) -> str:
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if audio.size == 0:
            return ""

        with self._lock:
            if self._sample_rate is None:
                self._sample_rate = sample_rate
            elif self._sample_rate != sample_rate:
                # Reamostra simples por proporção
                ratio = sample_rate / self._sample_rate
                audio = np.interp(
                    np.linspace(0, audio.size, int(audio.size / ratio), endpoint=False),
                    np.arange(audio.size),
                    audio,
                ).astype(np.float32)

            self._buffer = np.concatenate([self._buffer, audio])
            max_samples = int(self.config.max_history_seconds * self._sample_rate)
            if self._buffer.size > max_samples:
                drop = self._buffer.size - max_samples
                self._buffer = self._buffer[drop:]
                drop_seconds = drop / self._sample_rate
                self._last_segment_end = max(0.0, self._last_segment_end - drop_seconds)

            duration = self._buffer.size / self._sample_rate
            if self._last_segment_end == 0.0 and duration < self.config.min_window_seconds:
                return ""
            if duration - self._last_segment_end < self.config.min_increment_seconds:
                return ""

            segments, _ = self._model.transcribe(
                self._buffer,
                language=self.config.language,
                beam_size=1,
                best_of=1,
                vad_filter=True,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.5,
            )

            new_text_parts: list[str] = []
            new_end = self._last_segment_end
            for segment in segments:
                if segment.end <= self._last_segment_end + 0.05:
                    continue
                text = segment.text.strip()
                if text:
                    new_text_parts.append(text)
                new_end = max(new_end, float(segment.end))

            self._last_segment_end = new_end
            return " ".join(new_text_parts).strip()
