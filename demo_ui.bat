@echo off
REM Quick UI Demo - FlashSoft Interview Assistant
REM This script opens the UI so you can test the buttons and functionality

echo ========================================
echo  FlashSoft Interview Assistant - UI Demo
echo ========================================
echo.
echo Starting the UI...
echo.
echo Instructions:
echo   1. The UI will open in a new window
echo   2. Click "Browse..." buttons to load your files:
echo      - Resume: examples\manual_inputs\Resume-Gustavo-Marques Sep25.docx
echo      - Job Description: examples\manual_inputs\Technical Application ^&amp_ Integration Specialist .pdf
echo      - Audio (optional): examples\manual_inputs\captura_wasapi_autodetect.wav
echo   3. Use hotkeys:
echo      - Alt+S : Start session
echo      - Alt+G : Generate answer
echo      - Alt+E : End session
echo.
echo Press any key to launch the UI...
pause >nul

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m src.interview_assistant --ui

echo.
echo UI closed.
pause
