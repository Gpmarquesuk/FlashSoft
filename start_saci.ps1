# Script para iniciar SACI UI + Backend

Write-Host "Iniciando SACI System..." -ForegroundColor Cyan

# Carrega variaveis de ambiente
$env:OPENROUTER_API_KEY = (Get-Content .env | Select-String "OPENROUTER_API_KEY").ToString().Split('=')[1].Trim()
$env:OPENAI_API_KEY = (Get-Content .env | Select-String "OPENAI_API_KEY").ToString().Split('=')[1].Trim(' "')

Write-Host "OK - Variaveis carregadas" -ForegroundColor Green

# Inicia Backend
Write-Host "Iniciando Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:OPENROUTER_API_KEY='$env:OPENROUTER_API_KEY'; `$env:OPENAI_API_KEY='$env:OPENAI_API_KEY'; .\.venv\Scripts\python.exe -m uvicorn saci_server:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 5

# Inicia Frontend  
Write-Host "Iniciando Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:OPENROUTER_API_KEY='$env:OPENROUTER_API_KEY'; `$env:OPENAI_API_KEY='$env:OPENAI_API_KEY'; .\.venv\Scripts\streamlit run saci_ui/app.py --server.fileWatcherType none"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "SACI PRONTO!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Backend: http://127.0.0.1:8000" -ForegroundColor Cyan
