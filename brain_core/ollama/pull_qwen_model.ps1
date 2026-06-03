param(
    [string]$ModelName = "qwen2.5:3b"
)

$ErrorActionPreference = "Stop"

$ollamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
if (-not (Test-Path $ollamaExe)) {
    Write-Host "Ollama executable was not found at $ollamaExe"
    Write-Host "Install Ollama for Windows first, then rerun this script."
    exit 1
}

& "$PSScriptRoot\ensure_ollama_server.ps1"
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "Pulling Ollama model: $ModelName"
& $ollamaExe pull $ModelName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Model pull failed. You can rerun this command; Ollama usually resumes partial downloads."
    exit $LASTEXITCODE
}

Write-Host "Installed models:"
& $ollamaExe list
