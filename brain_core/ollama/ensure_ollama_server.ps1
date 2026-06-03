$ErrorActionPreference = "Stop"

function Resolve-OllamaExe {
    $cmd = Get-Command ollama -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $localExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path -LiteralPath $localExe) {
        return $localExe
    }

    throw "ollama command not found. Install Ollama or add it to PATH first."
}

function Test-OllamaServer {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 3 | Out-Null
        return $true
    } catch {
        return $false
    }
}

$ollamaExe = Resolve-OllamaExe
if (Test-OllamaServer) {
    Write-Host "Ollama server is already running."
    exit 0
}

$ollamaDir = Split-Path -Parent $ollamaExe
Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WorkingDirectory $ollamaDir -WindowStyle Hidden
Start-Sleep -Seconds 5

if (-not (Test-OllamaServer)) {
    throw "Ollama server did not respond at http://127.0.0.1:11434"
}

Write-Host "Ollama server started."
