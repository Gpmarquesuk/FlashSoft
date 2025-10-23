import string

import pytest
import tkinter as tk

from src.interview_assistant.ui.app import AssistantApp


@pytest.fixture
def app():
    try:
        assistant = AssistantApp()
    except tk.TclError as exc:
        pytest.skip(f"Tk not available: {exc}")
    try:
        assistant.root.update_idletasks()
        yield assistant
    finally:
        assistant.root.destroy()


def test_button_labels_are_ascii(app):
    for key in ("start", "generate", "end"):
        text = app._controls[key].cget("text")
        assert all(ch in string.printable for ch in text), f"Non-ASCII label detected: {text!r}"


def test_hotkeys_registered(app):
    for key in ("<Alt-s>", "<Alt-g>", "<Alt-e>"):
        assert key in app._hotkeys, f"{key} hotkey missing"


def test_layout_resizes_without_clipping(app):
    transcript_pack = app.transcript_box.pack_info()
    answer_pack = app.answer_box.pack_info()
    assert transcript_pack.get("fill") == "both"
    assert transcript_pack.get("expand") in (1, "1")
    assert answer_pack.get("fill") == "both"
    assert answer_pack.get("expand") in (1, "1")
