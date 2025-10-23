from pathlib import Path

from src.interview_assistant.ui.overlay import OverlayWindow, create_overlay_content


def test_overlay_headless(tmp_path: Path):
    overlay_path = tmp_path / "overlay.html"
    overlay = OverlayWindow(overlay_path=overlay_path, enable_gui=False)
    content = create_overlay_content(
        "Resposta teste",
        ["Use Whisper", "Foque em metricas", "Mencione experiencias"],
        ["curriculo", "job description"],
    )
    overlay.update(content)
    assert overlay_path.exists()
    html = overlay_path.read_text(encoding="utf-8")
    assert "Resposta teste" in html
    overlay.toggle_visibility(force=False)  # no-op headless
    overlay.mark_addressed()  # no-op headless
