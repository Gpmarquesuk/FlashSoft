import pytest
from unittest.mock import patch, Mock
from src.interview_assistant.overlay import Overlay

@pytest.fixture
def overlay():
    return Overlay()

@patch('src.interview_assistant.overlay.Tk')
def test_overlay_fallback(mock_tk, overlay):
    mock_tk.side_effect = Exception("Simulated failure")
    with patch('src.interview_assistant.overlay.save_html') as mock_save_html:
        overlay.display('topmost_window', 'Sample answer text')
        mock_save_html.assert_called_once_with('overlay.html', 'Sample answer text')

    # Test HTML generation
    with patch('src.interview_assistant.overlay.save_html') as mock_save_html:
        overlay.display('overlay_html', 'Sample answer text')
        mock_save_html.assert_called_once_with('overlay.html', 'Sample answer text')
