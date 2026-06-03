@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

set MODEL_NAME=%~1
if "%MODEL_NAME%"=="" set MODEL_NAME=qwen2.5:3b

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ollama\pull_qwen_model.ps1" -ModelName "%MODEL_NAME%"

pause
