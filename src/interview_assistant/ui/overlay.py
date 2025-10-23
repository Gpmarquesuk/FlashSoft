from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Iterable, Optional

try:
    import tkinter as tk
except ImportError:  # pragma: no cover
    tk = None


OVERLAY_TEMPLATE = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>FlashSoft Overlay</title>
  <style>
    :root {
      color-scheme: dark;
    }
    body {
      margin: 0;
      padding: 0;
      font-family: "Segoe UI", "Inter", sans-serif;
      background: transparent;
    }
    .layer {
      background: linear-gradient(135deg, rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.7));
      color: #e2e8f0;
      border-radius: 18px;
      padding: 24px 28px;
      min-width: 420px;
      box-shadow: 0 12px 40px rgba(2, 6, 23, 0.5);
      backdrop-filter: blur(12px);
    }
    .headline {
      font-size: 28px;
      line-height: 1.35;
      font-weight: 600;
      margin: 0 0 18px 0;
      text-shadow: 0 2px 12px rgba(8, 145, 178, 0.35);
    }
    .chips {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }
    .chip {
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid rgba(59, 130, 246, 0.45);
      color: #cbd5f5;
      border-radius: 999px;
      padding: 6px 12px;
      font-size: 13px;
      font-weight: 500;
    }
    .sources {
      font-size: 12px;
      color: #94a3b8;
      letter-spacing: 0.01em;
    }
  </style>
</head>
<body>
  <div class="layer">
    <div class="headline">$answer</div>
    <div class="chips">$talking_points</div>
    <div class="sources">$sources</div>
  </div>
</body>
</html>
""")


@dataclass
class OverlayContent:
    answer: str
    talking_points: Iterable[str]
    sources: Iterable[str]


class OverlayWindow:
    def __init__(
        self,
        overlay_path: Path,
        hotkey_toggle: str = "Ctrl+Alt+Space",
        hotkey_ack: str = "Ctrl+Alt+Enter",
        enable_gui: bool = True,
    ) -> None:
        self.overlay_path = overlay_path
        self.hotkey_toggle = hotkey_toggle
        self.hotkey_ack = hotkey_ack
        self._visible = True
        self._enable_gui = enable_gui and tk is not None
        self._lock = threading.Lock()
        self._latest: Optional[OverlayContent] = None
        self._queue: "queue.Queue[tuple[str, Optional[OverlayContent]]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None

        if self._enable_gui:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def update(self, content: OverlayContent) -> None:
        with self._lock:
            self._latest = content
        self._write_html(content)
        if self._enable_gui and self._thread is not None:
            self._queue.put(("update", content))

    def toggle_visibility(self, force: Optional[bool] = None) -> None:
        if not self._enable_gui or self._thread is None:
            return
        self._queue.put(("toggle", OverlayContent("", [], [])))  # payload unused

    def mark_addressed(self) -> None:
        if not self._enable_gui or self._thread is None:
            return
        self._queue.put(("ack", OverlayContent("", [], [])))

    def _run_loop(self) -> None:  # pragma: no cover - GUI thread
        root = tk.Tk()
        root.title("FlashSoft Overlay")
        root.attributes("-topmost", True)
        root.configure(bg="#000000")
        root.geometry("520x260+1000+80")
        root.wm_attributes("-alpha", 0.92)
        label = tk.Label(
            root,
            text="",
            justify=tk.LEFT,
            fg="#e2e8f0",
            bg="#000000",
            wraplength=460,
            font=("Segoe UI", 20, "bold"),
        )
        label.pack(padx=22, pady=24)

        def process_queue() -> None:
            try:
                while True:
                    action, payload = self._queue.get_nowait()
                    if action == "update" and payload is not None:
                        label.config(text=self._format_text(payload))
                        root.deiconify()
                    elif action == "toggle":
                        if root.state() == "withdrawn":
                            root.deiconify()
                        else:
                            root.withdraw()
                    elif action == "ack":
                        label.config(text="Prompt read.")
                        root.withdraw()
            except queue.Empty:
                pass
            root.after(100, process_queue)

        root.after(100, process_queue)
        root.mainloop()

    def _format_text(self, content: OverlayContent) -> str:
        points = "\n".join(f"• {tp}" for tp in content.talking_points if tp)
        sources = ", ".join(content.sources) if content.sources else ""
        return f"{content.answer}\n\n{points}\n\n{sources}"

    def _write_html(self, content: OverlayContent) -> None:
        chips = "".join(f"<span class='chip'>{tp}</span>" for tp in content.talking_points if tp)
        sources = "Sources: " + ", ".join(content.sources) if content.sources else ""
        html = OVERLAY_TEMPLATE.substitute(
            answer=content.answer,
            talking_points=chips,
            sources=sources,
        )
        self.overlay_path.parent.mkdir(parents=True, exist_ok=True)
        self.overlay_path.write_text(html, encoding="utf-8")


def create_overlay_content(answer: str, talking_points: Iterable[str], sources: Iterable[str]) -> OverlayContent:
    return OverlayContent(answer=answer, talking_points=list(talking_points), sources=list(sources))
