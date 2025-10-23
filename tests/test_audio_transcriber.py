import wave
from pathlib import Path
from typing import List

import numpy as np
import time

from src.interview_assistant.audio.live_transcriber import LiveAudioTranscriber, TranscriptEvent
from src.interview_assistant.audio.sources import FileAudioSource


class FakeWhisperClient:
    def __init__(self) -> None:
        self.calls: List[int] = []

    def transcribe_chunk(self, audio_bytes: bytes, sample_rate: int) -> str:
        self.calls.append(sample_rate)
        return "transcricao simulada"


def _make_wav(path: Path, duration: float = 1.0, sample_rate: int = 16_000) -> None:
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    data = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    pcm = (data * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())


def test_live_transcriber_emits_events(tmp_path: Path):
    wav_path = tmp_path / "sample.wav"
    _make_wav(wav_path)
    source = FileAudioSource(wav_path, chunk_duration=0.5)
    whisper = FakeWhisperClient()
    events: List[TranscriptEvent] = []

    transcriber = LiveAudioTranscriber(whisper_client=whisper, source=source)
    transcriber.start(events.append)
    try:
        deadline = time.time() + 2
        while len(events) < 2 and time.time() < deadline:
            time.sleep(0.05)
    finally:
        transcriber.stop()

    assert whisper.calls, "cliente Whisper deveria ter sido invocado"
    assert events, "deve ter emitido eventos de transcricao"
    for event in events:
        assert event.text == "transcricao simulada"
        assert event.latency_ms >= 0
