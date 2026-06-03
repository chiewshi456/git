@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.10+ or add python to PATH.
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ollama\ensure_ollama_server.ps1"
if errorlevel 1 (
  echo Ollama server could not be started.
  pause
  exit /b 1
)

echo.
echo Starting Mika Brain v2 with llama fallback models.
echo Chat model: mika-ai:0.1
echo Memory model: llama3.2:3b
echo.

python main_v2.py --llm ollama --ollama-model mika-ai:0.1 --memory-model llama3.2:3b --debug

pause
