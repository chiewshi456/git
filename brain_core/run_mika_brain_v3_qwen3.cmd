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
echo Starting Mika Brain v3 with qwen3:1.7b only.
echo Other installed models are not loaded unless this process asks for them.
echo Memory file: %~dp0data\mika_v3_memory.json
echo.

python main_v3.py --llm ollama --model qwen3:1.7b --debug

pause
