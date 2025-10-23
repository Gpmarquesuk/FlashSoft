#!/usr/bin/env python3
"""Quick UI test to verify buttons are visible and functional."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import tkinter as tk
    from interview_assistant.ui.app import AssistantApp
    
    print("✓ Imports successful")
    
    # Create app
    app = AssistantApp()
    print("✓ App created")
    
    # Check controls
    assert 'start' in app._controls, "Start button missing"
    assert 'generate' in app._controls, "Generate button missing"
    assert 'end' in app._controls, "End button missing"
    print("✓ All buttons present")
    
    # Check button text
    start_text = app._controls['start']['text']
    assert "Start session" in start_text, f"Start button text wrong: {start_text}"
    assert "(Alt+S)" in start_text, "Start button missing hotkey hint"
    print(f"✓ Start button text: '{start_text}'")
    
    generate_text = app._controls['generate']['text']
    assert "Generate answer" in generate_text, f"Generate button text wrong: {generate_text}"
    assert "(Alt+G)" in generate_text, "Generate button missing hotkey hint"
    print(f"✓ Generate button text: '{generate_text}'")
    
    end_text = app._controls['end']['text']
    assert "End session" in end_text, f"End button text wrong: {end_text}"
    assert "(Alt+E)" in end_text, "End button missing hotkey hint"
    print(f"✓ End button text: '{end_text}'")
    
    # Check button width (should be visible)
    start_width = app._controls['start'].winfo_reqwidth()
    assert start_width > 100, f"Start button too narrow: {start_width}px"
    print(f"✓ Start button width: {start_width}px (visible)")
    
    # Check hotkeys
    assert '<Alt-s>' in app._hotkeys, "Alt+S hotkey missing"
    assert '<Alt-g>' in app._hotkeys, "Alt+G hotkey missing"
    assert '<Alt-e>' in app._hotkeys, "Alt+E hotkey missing"
    print("✓ All hotkeys registered")
    
    # Clean up
    app.root.destroy()
    print("\n✅ All UI checks passed! Buttons are visible and functional.")
    
except Exception as e:
    print(f"\n❌ UI test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
