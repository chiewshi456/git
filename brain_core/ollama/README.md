# Ollama Mika Model

This folder prepares a local Ollama model variant based on:

```text
llama3.2:3b
```

It does not edit or duplicate raw model weights. Ollama creates a derived local model from `Modelfile.mika`.

## Current Machine Status

On this machine, Ollama is available at:

```text
C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe
```

The user PATH contains that directory. The current local Ollama service has:

```text
llama3.2:3b
mika-ai:0.1
```

For the standalone Windows zip, start the server with the Ollama install directory as the working directory:

```powershell
$ollamaDir = "$env:LOCALAPPDATA\Programs\Ollama"
Start-Process -FilePath "$ollamaDir\ollama.exe" -ArgumentList "serve" -WorkingDirectory $ollamaDir -WindowStyle Hidden
```

## Create The Model

After Ollama is running and `llama3.2:3b` is available:

```powershell
cd C:\Users\User\Documents\游戏project\brain_core
.\ollama\create_mika_model.ps1
```

This creates:

```text
mika-ai:0.1
```

Run it:

```powershell
.\ollama\run_mika_model.ps1
```

Or directly:

```powershell
ollama run mika-ai:0.1
```

## Manual Commands

```powershell
ollama pull llama3.2:3b
ollama create mika-ai:0.1 -f .\ollama\Modelfile.mika
ollama run mika-ai:0.1
```

## What This Changes

The derived model is taught Mika's base identity:

- knows it is AI
- does not pretend to be human
- does not invent a real body, address, or private life
- uses short Chinese conversational replies
- remembers the current preferred style: direct, short, natural, clever
- refuses safety-prohibited topics

Runtime memory from `data/memory.json` is now injected by `brain/ollama_client.py` when `BrainCore` runs with `--llm auto` or `--llm ollama`.
