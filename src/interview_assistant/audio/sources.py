from __future__ import annotations

import wave
from pathlib import Path
from typing import Optional

import numpy as np

from .live_transcriber import AudioSource


class FileAudioSource(AudioSource):
    """
    AudioSource que lê um arquivo WAV e gera chunks de duração fixa.
    Útil para testes automatizados.
    """

    def __init__(self, path: Path, chunk_duration: float = 1.0):
        self.path = Path(path)
        self.chunk_duration = chunk_duration
        self.sample_rate: int = 16_000
        self._frames_per_chunk: int = 0
        self._wave: Optional[wave.Wave_read] = None

    def start(self) -> None:
        self._wave = wave.open(str(self.path), "rb")
        self.sample_rate = self._wave.getframerate()
        channels = self._wave.getnchannels()
        assert channels == 1, "Somente mono é suportado nos testes."
        self._frames_per_chunk = int(self.sample_rate * self.chunk_duration)

    def stop(self) -> None:
        if self._wave:
            self._wave.close()
            self._wave = None

    def read_chunk(self, timeout: float | None = None) -> bytes:
        if self._wave is None:
            raise RuntimeError("Fonte ainda não iniciada.")
        frames = self._wave.readframes(self._frames_per_chunk)
        if not frames:
            raise EOFError
        data = np.frombuffer(frames, dtype=np.int16)
        return data.tobytes()
