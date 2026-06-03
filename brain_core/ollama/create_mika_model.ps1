$ErrorActionPreference = "Stop"

$modelName = "mika-ai:0.1"
$modelfile = Join-Path $PSScriptRoot "Modelfile.mika"

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

function Start-OllamaServer {
    param([string]$OllamaExe)

    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 3 | Out-Null
        return
    } catch {
        $ollamaDir = Split-Path -Parent $OllamaExe
        Start-Process -FilePath $OllamaExe -ArgumentList "serve" -WorkingDirectory $ollamaDir -WindowStyle Hidden
        Start-Sleep -Seconds 5
        Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/version" -TimeoutSec 10 | Out-Null
    }
}

$ollamaExe = Resolve-OllamaExe
Start-OllamaServer -OllamaExe $ollamaExe

Push-Location (Split-Path -Parent $ollamaExe)
try {
    & $ollamaExe show llama3.2:3b | Out-Null
    & $ollamaExe create $modelName -f $modelfile
} finally {
    Pop-Location
}

Write-Host "Created $modelName"
Write-Host "Run: ollama run $modelName"
