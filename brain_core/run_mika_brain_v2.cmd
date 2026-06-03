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
echo Starting Mika Brain v2.
echo Brain v2 uses structured understanding before replying.
echo Memory file: %~dp0data\memory.json
echo.

python main_v2.py --llm ollama --ollama-model auto --memory-model auto --debug

pause
