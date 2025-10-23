from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - requires GUI environment
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except ImportError:  # pragma: no cover - headless environments
    tk = None
    filedialog = None
    messagebox = None
    ttk = None
    ScrolledText = None

from ..audio.live_transcriber import TranscriptEvent
from ..orchestration.pipeline import InterviewAssistant, InterviewAssistantConfig


@dataclass
class UIState:
    resume_path: Optional[Path] = None
    jd_path: Optional[Path] = None
    audio_path: Optional[Path] = None
    model: str = "openai/gpt-4o-mini"
    overlay_enabled: bool = True
    auto_generate: bool = False
    audio_chunk_duration: float = 1.0
    use_microphone: bool = False


class AssistantApp:
    POLL_INTERVAL_MS = 150

    def __init__(self) -> None:
        if tk is None:
            raise RuntimeError("tkinter is not available in this environment.")

        self.root = tk.Tk()
        self.root.title("FlashSoft Interview Assistant - MVP")
        self.root.geometry("1024x720")

        self.state = UIState()
        self.assistant: Optional[InterviewAssistant] = None
        self._session_thread: Optional[threading.Thread] = None
        self._running = False
        self._controls: dict[str, ttk.Button] = {}
        self._hotkeys: dict[str, str] = {}

        self.transcript_queue: "queue.Queue[TranscriptEvent]" = queue.Queue()
        self.answer_queue: "queue.Queue[dict]" = queue.Queue()
        self.status_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._last_transcript_text: str = ""

        self.resume_var = tk.StringVar()
        self.jd_var = tk.StringVar()
        self.audio_var = tk.StringVar()
        self.model_var = tk.StringVar(value=self.state.model)
        self.overlay_var = tk.BooleanVar(value=self.state.overlay_enabled)
        self.auto_var = tk.BooleanVar(value=self.state.auto_generate)
        self.chunk_var = tk.StringVar(value=str(self.state.audio_chunk_duration))
        self.microphone_var = tk.BooleanVar(value=self.state.use_microphone)
        self.status_var = tk.StringVar(value="Awaiting configuration.")

        self._init_style()

        self.question_entry = ttk.Entry(self.root, width=84, font=("Segoe UI", 11))
        self.transcript_box = ScrolledText(
            self.root,
            height=12,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 11),
            background="#141b2b",
            foreground="#e2e8f0",
            insertbackground="#e2e8f0",
        )
        self.answer_box = ScrolledText(
            self.root,
            height=12,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 11),
            background="#141b2b",
            foreground="#e2e8f0",
            insertbackground="#e2e8f0",
        )

        self._build_layout()
        self.root.after(self.POLL_INTERVAL_MS, self._poll_queues)

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _init_style(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        bg = "#0f172a"
        panel = "#111c2f"
        card = "#141f33"
        accent = "#3b82f6"
        text = "#e2e8f0"
        muted = "#94a3b8"

        self.root.configure(bg=bg)
        style.configure("Root.TFrame", background=bg)
        style.configure("Panel.TFrame", background=panel)
        style.configure(
            "Card.TLabelframe",
            background=card,
            foreground=text,
            borderwidth=1,
            relief="solid",
            bordercolor="#1f2a3d",
            padding=10,
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=card,
            foreground=text,
            font=("Segoe UI Semibold", 11),
        )
        style.configure("Header.TLabel", background=bg, foreground=text, font=("Segoe UI", 20, "bold"))
        style.configure("SubHeader.TLabel", background=bg, foreground=muted, font=("Segoe UI", 11))
        style.configure("TLabel", background=card, foreground=text, font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=bg, foreground=muted, font=("Segoe UI", 9))

        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#0b1120",
            font=("Segoe UI Semibold", 10),
            padding=8,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#2563eb"), ("pressed", "#1d4ed8")],
            foreground=[("disabled", "#1e293b")],
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.configure("TEntry", fieldbackground="#0b1628", background="#0b1628", foreground=text, borderwidth=0)
        style.configure("TCheckbutton", background=card, foreground=text, font=("Segoe UI", 10))
        style.map("TCheckbutton", foreground=[("disabled", "#475569")])

    def _build_layout(self) -> None:
        self.root.minsize(960, 640)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        root_frame = ttk.Frame(self.root, style="Root.TFrame")
        root_frame.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)

        header = ttk.Frame(root_frame, style="Root.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ttk.Label(header, text="FlashSoft Interview Assistant", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text="Real-time interview companion orchestrated by the FlashSoft factory",
            style="SubHeader.TLabel",
        ).pack(anchor=tk.W, pady=(4, 0))

        paned = ttk.Panedwindow(root_frame, orient=tk.VERTICAL)
        paned.grid(row=1, column=0, sticky="nsew")

        top_panel = ttk.Frame(paned, style="Panel.TFrame")
        bottom_panel = ttk.Frame(paned, style="Panel.TFrame")
        paned.add(top_panel, weight=1)
        paned.add(bottom_panel, weight=2)

        self._build_document_inputs(top_panel)
        self._build_configuration(top_panel)
        self._build_question_panel(top_panel)
        self._build_controls(top_panel)

        bottom_split = ttk.Panedwindow(bottom_panel, orient=tk.VERTICAL)
        bottom_split.pack(fill=tk.BOTH, expand=True)

        transcript_container = ttk.Frame(bottom_split, style="Panel.TFrame")
        answer_container = ttk.Frame(bottom_split, style="Panel.TFrame")
        bottom_split.add(transcript_container, weight=3)
        bottom_split.add(answer_container, weight=2)

        self._build_transcript_panel(transcript_container)
        self._build_answer_panel(answer_container)

    def _build_document_inputs(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Document Inputs", style="Card.TLabelframe")
        frame.pack(fill=tk.X, pady=(0, 12))
        self._add_file_picker(frame, "Resume (.pdf / .docx)", self.resume_var, self._choose_resume)
        self._add_file_picker(frame, "Job description (.pdf / .docx)", self.jd_var, self._choose_jd)
        self._add_file_picker(frame, "Interview audio (WAV optional)", self.audio_var, self._choose_audio)

    def _build_configuration(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Session Configuration", style="Card.TLabelframe")
        frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(frame, text="OpenRouter model:").grid(row=0, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.model_var, width=42).grid(row=0, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Label(frame, text="Audio chunk duration (seconds):").grid(row=1, column=0, sticky=tk.W, padx=6, pady=4)
        ttk.Entry(frame, textvariable=self.chunk_var, width=12).grid(row=1, column=1, sticky=tk.W, padx=6, pady=4)

        ttk.Checkbutton(
            frame,
            text="Show overlay window",
            variable=self.overlay_var,
        ).grid(row=0, column=2, sticky=tk.W, padx=16, pady=4)
        ttk.Checkbutton(
            frame,
            text="Auto-generate answer when a question is detected in audio",
            variable=self.auto_var,
        ).grid(row=1, column=2, sticky=tk.W, padx=16, pady=4)
        ttk.Checkbutton(
            frame,
            text="Capture microphone input (WASAPI)",
            variable=self.microphone_var,
        ).grid(row=0, column=3, sticky=tk.W, padx=16, pady=4)

    def _build_question_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Current Question", style="Card.TLabelframe")
        frame.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(frame, text="Question (auto-filled from audio when available):").pack(anchor=tk.W, padx=6, pady=(0, 6))
        self.question_entry.pack(in_=frame, fill=tk.X, padx=6, pady=(0, 4))

    def _build_controls(self, parent: ttk.Frame) -> None:
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.pack(fill=tk.X, pady=(0, 12))
        start_button = tk.Button(frame, text="Start session (Alt+S)", command=self.start_session, width=22)
        start_button.pack(side=tk.LEFT, padx=(0, 8), pady=6)

        generate_button = tk.Button(frame, text="Generate answer (Alt+G)", command=self.request_answer, width=22)
        generate_button.pack(side=tk.LEFT, padx=8, pady=6)

        end_button = tk.Button(frame, text="End session (Alt+E)", command=self.stop_session, width=22)
        end_button.pack(side=tk.LEFT, padx=8, pady=6)

        self._controls = {
            "start": start_button,
            "generate": generate_button,
            "end": end_button,
        }
        self._hotkeys.update(
            {
                "<Alt-s>": "Start session",
                "<Alt-g>": "Generate answer",
                "<Alt-e>": "End session",
            }
        )

        self.root.bind_all("<Alt-s>", self._on_hotkey_start, add="+")
        self.root.bind_all("<Alt-g>", self._on_hotkey_generate, add="+")
        self.root.bind_all("<Alt-e>", self._on_hotkey_end, add="+")

        self.status_label = ttk.Label(frame, textvariable=self.status_var, style="Muted.TLabel")
        self.status_label.pack(side=tk.LEFT, padx=16)

    def _build_transcript_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Live Transcription", style="Card.TLabelframe")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
        self.transcript_box.configure(borderwidth=0)
        self.transcript_box.pack(in_=frame, fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _build_answer_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Latest Answer", style="Card.TLabelframe")
        frame.pack(fill=tk.BOTH, expand=True)
        self.answer_box.configure(borderwidth=0)
        self.answer_box.pack(in_=frame, fill=tk.BOTH, expand=True, padx=6, pady=6)

    def _add_file_picker(self, parent: ttk.Labelframe, label: str, var: tk.StringVar, callback) -> None:
        row = len(parent.grid_slaves()) // 3
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=5)
        entry = ttk.Entry(parent, textvariable=var, width=82)
        entry.grid(row=row, column=1, sticky=tk.W, padx=6, pady=5)
        ttk.Button(parent, text="Browse…", command=callback).grid(row=row, column=2, sticky=tk.W, padx=6, pady=5)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------
    def _choose_resume(self) -> None:
        if filedialog is None:
            return
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.docx")])
        if path:
            self.resume_var.set(path)

    def _choose_jd(self) -> None:
        if filedialog is None:
            return
        path = filedialog.askopenfilename(filetypes=[("Documents", "*.pdf *.docx")])
        if path:
            self.jd_var.set(path)

    def _choose_audio(self) -> None:
        if filedialog is None:
            return
        path = filedialog.askopenfilename(filetypes=[("WAV audio", "*.wav")])
        if path:
            self.audio_var.set(path)

    def start_session(self) -> None:
        if self._running:
            messagebox.showinfo("Session in progress", "A session is already running.")
            return
        try:
            resume = Path(self.resume_var.get()).expanduser()
            jd = Path(self.jd_var.get()).expanduser()
        except Exception:
            messagebox.showerror("Missing files", "Select both resume and job description files.")
            return

        if not resume.exists() or not jd.exists():
            messagebox.showerror("Invalid files", "Resume or job description path is not valid.")
            return

        audio_path = Path(self.audio_var.get()).expanduser() if self.audio_var.get() else None
        if audio_path and not audio_path.exists():
            messagebox.showerror("Invalid audio", "The selected audio file does not exist.")
            return

        try:
            chunk_duration = float(self.chunk_var.get())
            if chunk_duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid duration", "Audio chunk duration must be a positive number.")
            return

        self.state = UIState(
            resume_path=resume,
            jd_path=jd,
            audio_path=audio_path,
            model=self.model_var.get().strip() or "openai/gpt-4o-mini",
            overlay_enabled=self.overlay_var.get(),
            auto_generate=self.auto_var.get(),
            audio_chunk_duration=chunk_duration,
            use_microphone=self.microphone_var.get(),
        )

        self._running = True
        self.status_var.set("Starting session…")
        self._session_thread = threading.Thread(target=self._bootstrap_session, daemon=True)
        self._session_thread.start()

    def _bootstrap_session(self) -> None:
        try:
            config = InterviewAssistantConfig(
                resume_path=self.state.resume_path,
                jd_path=self.state.jd_path,
                output_dir=Path("artifacts"),
                logs_dir=Path("logs"),
                overlay_path=Path("artifacts") / "overlay.html",
                model=self.state.model,
                question=None,
                enable_audio=self.state.audio_path is not None or self.state.use_microphone,
                enable_overlay_gui=self.state.overlay_enabled,
                audio_path=self.state.audio_path,
                audio_chunk_duration=self.state.audio_chunk_duration,
                auto_generate_on_chunk=self.state.auto_generate,
            )
            assistant = InterviewAssistant(config)
            assistant.add_transcript_listener(self._enqueue_transcript)
            assistant.add_answer_listener(self._enqueue_answer)
            assistant.bootstrap()
            self.assistant = assistant

            if self.state.audio_path:
                status_msg = "Session running with audio file. Transcribing questions from the selected WAV."
            elif self.state.use_microphone:
                status_msg = "Session running with WASAPI microphone. Speak to test real-time transcription."
            else:
                status_msg = "Session started. Provide a question or wait for the transcription."
            self.status_queue.put(("info", status_msg))
        except Exception as exc:  # pragma: no cover - GUI feedback
            self._running = False
            self.assistant = None
            self.status_queue.put(("error", f"Failed to start session: {exc}"))

    def stop_session(self) -> None:
        if not self._running:
            self.status_var.set("No active session.")
            return
        threading.Thread(target=self._shutdown_session, daemon=True).start()

    def _shutdown_session(self) -> None:
        try:
            if self.assistant:
                self.assistant.shutdown()
        finally:
            self.assistant = None
            self._running = False
            self.status_queue.put(("info", "Session ended."))

    # ------------------------------------------------------------------
    # Answer generation
    # ------------------------------------------------------------------
    def request_answer(self) -> None:
        if not self.assistant:
            messagebox.showwarning("Session not started", "Start the session before generating answers.")
            return
        question = self.question_entry.get().strip()
        if not question:
            question = self._last_transcript_text.strip()
        if not question:
            messagebox.showwarning("Question missing", "Provide the question manually or wait for the transcription.")
            return
        self.status_queue.put(("info", "Generating answer…"))
        threading.Thread(target=self._generate_answer, args=(question,), daemon=True).start()

    def _generate_answer(self, question: str) -> None:
        try:
            self.assistant.generate_answer(question)
            self.status_queue.put(("success", "Answer generated. Overlay and panel updated."))
        except Exception as exc:
            self.status_queue.put(("error", f"Failed to generate answer: {exc}"))

    # ------------------------------------------------------------------
    # Queue adapters (transcripts & answers)
    # ------------------------------------------------------------------
    def _enqueue_transcript(self, event: TranscriptEvent) -> None:
        self.transcript_queue.put(event)

    def _enqueue_answer(self, payload: dict) -> None:
        self.answer_queue.put(payload)

    # ------------------------------------------------------------------
    # Event loop
    # ------------------------------------------------------------------
    def _poll_queues(self) -> None:
        updated_question = False
        while True:
            try:
                event = self.transcript_queue.get_nowait()
            except queue.Empty:
                break
            text = event.text.strip()
            if text:
                self._append_transcript(text)
                self._last_transcript_text = text
                if "?" in text and not self.question_entry.get().strip():
                    self.question_entry.delete(0, tk.END)
                    self.question_entry.insert(0, text)
                    updated_question = True

        while True:
            try:
                payload = self.answer_queue.get_nowait()
            except queue.Empty:
                break
            self._show_answer(payload)

        while True:
            try:
                level, message = self.status_queue.get_nowait()
            except queue.Empty:
                break
            self._update_status(level, message)

        self.root.after(self.POLL_INTERVAL_MS, self._poll_queues)
        if updated_question and self.state.auto_generate and self.assistant:
            self.request_answer()

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _append_transcript(self, text: str) -> None:
        self.transcript_box.configure(state=tk.NORMAL)
        self.transcript_box.insert(tk.END, text + "\n")
        self.transcript_box.see(tk.END)
        self.transcript_box.configure(state=tk.DISABLED)

    def _show_answer(self, payload: dict) -> None:
        answer = payload.get("final_answer", "")
        talking_points = payload.get("talking_points", [])
        sources = payload.get("sources", [])

        rendered = [
            f"Question: {payload.get('question', self.question_entry.get())}",
            "",
            "Suggested answer:",
            answer,
            "",
            "Key talking points:",
        ]
        rendered.extend(f"- {tp}" for tp in talking_points)
        rendered.append("")
        rendered.append(f"Sources: {', '.join(sources) if sources else 'not specified'}")

        self.answer_box.configure(state=tk.NORMAL)
        self.answer_box.delete("1.0", tk.END)
        self.answer_box.insert(tk.END, "\n".join(rendered))
        self.answer_box.configure(state=tk.DISABLED)

    def _update_status(self, level: str, message: str) -> None:
        colours = {
            "success": "#34d399",
            "error": "#f87171",
            "info": "#60a5fa",
        }
        colour = colours.get(level, "#94a3b8")
        self.status_label.configure(foreground=colour, text=message)
        self.status_var.set(message)

    def _on_hotkey_start(self, event: tk.Event) -> str:
        self.start_session()
        return "break"

    def _on_hotkey_generate(self, event: tk.Event) -> str:
        self.request_answer()
        return "break"

    def _on_hotkey_end(self, event: tk.Event) -> str:
        self.stop_session()
        return "break"

    def run(self) -> None:
        self.root.mainloop()


def launch_app() -> None:
    app = AssistantApp()
    app.run()


