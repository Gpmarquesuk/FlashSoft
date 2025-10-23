from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol

import numpy as np

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - dependerá do ambiente
    sd = None


class WhisperClient(Protocol):
    def transcribe_chunk(self, audio_bytes: bytes, sample_rate: int) -> str: ...


class AudioSource(Protocol):
    sample_rate: int
    chunk_duration: float

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def read_chunk(self, timeout: float | None = None) -> bytes: ...


@dataclass
class TranscriptEvent:
    text: str
    start_time: float
    end_time: float
    latency_ms: float


class MicrophoneSource:
    """
    Captura áudio do microfone usando sounddevice, convertendo em chunks PCM.
    """

    def __init__(self, sample_rate: int = 16_000, channels: int = 1, chunk_duration: float = 1.0):
        if sd is None:
            raise RuntimeError(
                "sounddevice não está disponível. Instale o pacote ou forneça um AudioSource customizado."
            )
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.frames_per_chunk = int(sample_rate * chunk_duration)
        self._queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=5)
        self._stream: Optional[sd.InputStream] = None
        self._device_index: Optional[int] = None

    def _resolve_wasapi_device(self) -> int:
        hostapi_index = None
        for idx, api in enumerate(sd.query_hostapis()):
            if "windows wasapi" in api["name"].lower():
                hostapi_index = idx
                break
        if hostapi_index is None:
            raise RuntimeError(
                "Host API 'Windows WASAPI' não encontrado. "
                "Verifique instalação do sounddevice e drivers WASAPI."
            )

        devices = sd.query_devices()
        candidates = [
            dev for dev in devices if dev["hostapi"] == hostapi_index and dev["max_input_channels"] >= self.channels
        ]
        if not candidates:
            raise RuntimeError("Nenhum dispositivo WASAPI disponível com canais de entrada suficientes.")
        # Seleciona o primeiro dispositivo padrão de entrada
        for dev in candidates:
            if dev.get("default_samplerate"):
                return dev["index"]
        return candidates[0]["index"]

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            # apenas registrar; o pipeline pode usar observability para logar
            print(f"[audio] warning: {status}")
        self._queue.put(indata.copy())

    def start(self) -> None:
        try:
            self._device_index = self._resolve_wasapi_device()
        except Exception as exc:
            raise RuntimeError(f"Erro ao localizar dispositivo WASAPI: {exc}") from exc

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            blocksize=self.frames_per_chunk,
            callback=self._callback,
            device=self._device_index,
            latency="low",
        )
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        while not self._queue.empty():
            self._queue.get_nowait()

    def read_chunk(self, timeout: float | None = None) -> bytes:
        data = self._queue.get(timeout=timeout)
        return (data.astype(np.int16)).tobytes()


class LiveAudioTranscriber:
    """
    Recebe chunks de áudio de um AudioSource, envia ao WhisperClient e emite eventos TranscriptEvent.
    """

    def __init__(
        self,
        whisper_client: WhisperClient,
        source: Optional[AudioSource] = None,
        metrics_callback: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.whisper_client = whisper_client
        self.source = source or MicrophoneSource()
        self.metrics_callback = metrics_callback
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()
        self._completed = threading.Event()

    def start(self, on_transcript: Callable[[TranscriptEvent], None]) -> None:
        if self._thread and self._thread.is_alive():
            raise RuntimeError("Transcriber já está em execução.")
        reset_fn = getattr(self.whisper_client, "reset", None)
        if callable(reset_fn):
            reset_fn()
        self.source.start()
        self._running.set()
        self._completed.clear()
        self._thread = threading.Thread(
            target=self._process_loop,
            args=(on_transcript,),
            name="live-audio-transcriber",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        self.source.stop()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        self._completed.set()

    def join(self, timeout: float | None = None) -> bool:
        return self._completed.wait(timeout=timeout)

    def _process_loop(self, on_transcript: Callable[[TranscriptEvent], None]) -> None:
        chunk_index = 0
        while self._running.is_set():
            try:
                started = time.time()
                chunk = self.source.read_chunk(timeout=1.5)
            except queue.Empty:
                continue
            except EOFError:
                self._running.clear()
                break
            except Exception as exc:  # pragma: no cover - defensive log
                print(f"[audio] erro capturando audio: {exc}")
                continue

            if not chunk:
                continue

            try:
                whisper_start = time.time()
                text = self.whisper_client.transcribe_chunk(chunk, self.source.sample_rate)
                latency_ms = (time.time() - whisper_start) * 1000.0
            except Exception as exc:
                print(f"[audio] erro transcrevendo chunk: {exc}")
                continue

            event = TranscriptEvent(
                text=text.strip(),
                start_time=chunk_index * self.source.chunk_duration,
                end_time=(chunk_index + 1) * self.source.chunk_duration,
                latency_ms=latency_ms,
            )
            chunk_index += 1

            if self.metrics_callback:
                self.metrics_callback(
                    "latency_transcription_ms",
                    latency_ms,
                    chunk_index=chunk_index,
                    timestamp=time.time(),
                )

            on_transcript(event)
        try:
            self.source.stop()
        except Exception:
            pass
        self._completed.set()
