from __future__ import annotations

import argparse
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional

from dotenv import load_dotenv

from ..audio.live_transcriber import LiveAudioTranscriber, TranscriptEvent
from ..audio.whisper_client import OpenRouterWhisperClient
from ..audio.sources import FileAudioSource
from ..documents.parser import DocumentParser
from ..generation.assistant import GenerationConfig, InterviewResponseGenerator
from ..observability.logger import JSONLLogger, MetricsCollector
from ..retrieval.vector_store import VectorStore
from ..ui.overlay import OverlayContent, OverlayWindow, create_overlay_content


load_dotenv()


@dataclass
class InterviewAssistantConfig:
    resume_path: Path
    jd_path: Path
    output_dir: Path
    logs_dir: Path
    overlay_path: Path
    question: Optional[str]
    model: str = "openai/gpt-4o-mini"
    enable_audio: bool = True
    enable_overlay_gui: bool = True
    audio_path: Optional[Path] = None
    audio_chunk_duration: float = 1.0
    auto_generate_on_chunk: bool = False


@dataclass
class AssistantState:
    transcript: List[str] = field(default_factory=list)
    last_answer: Optional[dict] = None
    last_question: Optional[str] = None


class InterviewAssistant:
    def __init__(self, config: InterviewAssistantConfig) -> None:
        self.config = config
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir = config.logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        self.doc_parser = DocumentParser()
        self.vector_store = VectorStore(top_k=5)
        self.generator = InterviewResponseGenerator(
            GenerationConfig(model=config.model)
        )
        self.transcript_logger = JSONLLogger(self.logs_dir / "live_transcript.jsonl")
        self.metrics = MetricsCollector(self.logs_dir / "metrics.jsonl")
        self.overlay = OverlayWindow(
            overlay_path=config.overlay_path,
            enable_gui=config.enable_overlay_gui,
        )
        self.state = AssistantState()
        self._transcriber: Optional[LiveAudioTranscriber] = None
        self._transcript_listeners: List[Callable[[TranscriptEvent], None]] = []
        self._answer_listeners: List[Callable[[dict], None]] = []
        self._corpus: dict[str, List[str]] = {}

    def bootstrap(self) -> None:
        parsed = self.doc_parser.parse_both(self.config.resume_path, self.config.jd_path)
        resume_sections = parsed["resume"]["sections"]
        jd_sections = parsed["job_description"]["sections"]

        corpus = {
            "resume": [" ".join(lines) for lines in resume_sections.values()],
            "job_description": [" ".join(lines) for lines in jd_sections.values()],
        }
        self._corpus = corpus
        self.vector_store.build_index(corpus)

        if self.config.enable_audio:
            whisper_client = OpenRouterWhisperClient()
            audio_source = None
            if self.config.audio_path:
                audio_source = FileAudioSource(
                    self.config.audio_path,
                    chunk_duration=self.config.audio_chunk_duration,
                )
            self._transcriber = LiveAudioTranscriber(
                whisper_client=whisper_client,
                source=audio_source,
                metrics_callback=self.metrics.record,
            )
            self._transcriber.start(self._on_transcript)

    def shutdown(self) -> None:
        if self._transcriber:
            self._transcriber.stop()

    def _on_transcript(self, event: TranscriptEvent) -> None:
        payload = {
            "type": "transcript_chunk",
            "text": event.text,
            "start": event.start_time,
            "end": event.end_time,
            "latency_ms": event.latency_ms,
        }
        self.transcript_logger.log(payload)
        if event.text:
            self.state.transcript.append(event.text)
            if len(self.state.transcript) > 50:
                self.state.transcript = self.state.transcript[-50:]
        for listener in list(self._transcript_listeners):
            try:
                listener(event)
            except Exception as exc:  # pragma: no cover - defensivo
                print(f"[assistant] transcript listener error: {exc}")
        if self.config.auto_generate_on_chunk:
            chunk_text = event.text.strip()
            if chunk_text and ("?" in chunk_text or len(chunk_text.split()) >= 6):
                self._schedule_answer(chunk_text)

    def add_transcript_listener(self, callback: Callable[[TranscriptEvent], None]) -> None:
        self._transcript_listeners.append(callback)

    def add_answer_listener(self, callback: Callable[[dict], None]) -> None:
        self._answer_listeners.append(callback)

    def wait_for_transcription_end(self, timeout: Optional[float] = None) -> bool:
        if not self._transcriber:
            return True
        return self._transcriber.join(timeout=timeout)

    def _schedule_answer(self, question: str) -> None:
        threading.Thread(
            target=self.generate_answer,
            args=(question,),
            daemon=True,
        ).start()

    def run_once(self) -> dict:
        self.bootstrap()
        try:
            answer_payload = self.generate_answer(self.config.question)
            return answer_payload
        finally:
            self.shutdown()

    def generate_answer(self, question: Optional[str] = None) -> dict:
        question = (question or self.config.question or "").strip()
        if not question:
            raise ValueError("Nenhuma pergunta informada para gerar a resposta.")
        self.state.last_question = question
        retrieval_results = self.vector_store.query(question)
        resume_chunks = [chunk.text for chunk in retrieval_results if chunk.source == "resume"]
        jd_chunks = [chunk.text for chunk in retrieval_results if chunk.source != "resume"]
        if not resume_chunks and "resume" in self._corpus:
            resume_chunks = self._corpus["resume"][:3]
        if not jd_chunks and "job_description" in self._corpus:
            jd_chunks = self._corpus["job_description"][:3]
        payload = self.generator.generate(
            question=question,
            resume_chunks=resume_chunks,
            jd_chunks=jd_chunks,
            transcript=self.state.transcript,
        )
        self._handle_answer(payload, question)
        payload_with_question = dict(payload)
        payload_with_question.setdefault("question", question)
        return payload_with_question

    def _handle_answer(self, payload: dict, question: str) -> None:
        final_answer = payload.get("final_answer") or payload.get("answer") or ""
        talking_points = payload.get("talking_points", []) or []
        sources = payload.get("sources", []) or []
        overlay_content = create_overlay_content(final_answer, talking_points, sources)
        self.overlay.update(overlay_content)

        artifact = {
            "question": question,
            "final_answer": final_answer,
            "talking_points": list(talking_points),
            "sources": list(sources),
            "timestamp": time.time(),
        }
        (self.output_dir / "last_answer.json").write_text(
            json.dumps(artifact, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.metrics.record("response_generated", 1)
        self.state.last_answer = artifact
        for listener in list(self._answer_listeners):
            try:
                listener(artifact)
            except Exception as exc:  # pragma: no cover - defensivo
                print(f"[assistant] answer listener error: {exc}")


def run_cli(
    resume: Path,
    jd: Path,
    question: Optional[str],
    output_dir: Path,
    logs_dir: Path,
    model: str = "openai/gpt-4o-mini",
    enable_audio: bool = True,
    enable_overlay_gui: bool = True,
    audio_path: Optional[Path] = None,
    auto_generate_on_chunk: bool = False,
    audio_chunk_duration: float = 1.0,
) -> dict:
    config = InterviewAssistantConfig(
        resume_path=resume,
        jd_path=jd,
        output_dir=output_dir,
        logs_dir=logs_dir,
        overlay_path=output_dir / "overlay.html",
        model=model,
        question=question,
        enable_audio=enable_audio,
        enable_overlay_gui=enable_overlay_gui,
        audio_path=audio_path,
        audio_chunk_duration=audio_chunk_duration,
        auto_generate_on_chunk=auto_generate_on_chunk,
    )
    assistant = InterviewAssistant(config)
    try:
        assistant.bootstrap()
        result = assistant.generate_answer(question)
        if audio_path:
            time.sleep(max(config.audio_chunk_duration, 1.5))
        return result
    finally:
        assistant.shutdown()


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="FlashSoft Interview Assistant")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--jd", type=Path)
    parser.add_argument("--question")
    parser.add_argument("--output-dir", default=Path("artifacts"), type=Path)
    parser.add_argument("--logs-dir", default=Path("logs"), type=Path)
    parser.add_argument("--model", default="openai/gpt-4o-mini")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--headless-overlay", action="store_true")
    parser.add_argument("--audio-file", type=Path, help="Arquivo WAV para simular audio da entrevista.")
    parser.add_argument("--auto-from-audio", action="store_true", help="Gera resposta automaticamente ao detectar pergunta no audio.")
    parser.add_argument("--audio-chunk-duration", type=float, default=1.0, help="Duração (s) dos chunks de audio.")
    parser.add_argument("--ui", action="store_true", help="Inicia a interface gráfica interativa.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.ui:
        from ..ui.app import launch_app

        launch_app()
        return

    if not args.resume or not args.jd or not args.question:
        parser.error("--resume, --jd e --question são obrigatórios no modo CLI.")

    audio_path = args.audio_file if args.audio_file and not args.no_audio else None
    payload = run_cli(
        resume=args.resume,
        jd=args.jd,
        question=args.question,
        output_dir=args.output_dir,
        logs_dir=args.logs_dir,
        model=args.model,
        enable_audio=not args.no_audio,
        enable_overlay_gui=not args.headless_overlay,
        audio_path=audio_path,
        auto_generate_on_chunk=args.auto_from_audio,
        audio_chunk_duration=args.audio_chunk_duration,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


