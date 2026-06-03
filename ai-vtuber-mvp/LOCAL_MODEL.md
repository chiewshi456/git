# Local Model Setup

This project can use Ollama as a local model backend. It does not require an OpenAI API key.

## Current PC Check

Your `nvidia-smi` output shows:

- GPU: NVIDIA GeForce RTX 5060 Laptop GPU
- VRAM: 8151 MiB
- Driver: 596.49
- CUDA reported by driver: 13.2

For this class of GPU, start with a small Chinese-capable model:

```powershell
ollama pull qwen3:4b
```

`qwen3:4b` is a good first choice because it is much lighter than 8B+ models and is strong enough for short VTuber chat replies.

## Install Ollama

Install Ollama for Windows from the official docs:

```text
https://docs.ollama.com/windows
```

After installation, confirm it works:

```powershell
ollama --version
ollama pull qwen3:4b
ollama run qwen3:4b
```

Ollama serves a local API at:

```text
http://localhost:11434
```

## Enable Ollama In This Project

Edit:

```text
config/localModel.json
```

Change:

```json
"provider": "mock"
```

to:

```json
"provider": "ollama"
```

Keep this first model setting:

```json
"model": "qwen3:4b"
```

Then restart:

```powershell
pnpm dev
```

## Safety Behavior

The flow stays the same:

```text
message
-> inputSafetyCheck
-> MessageSelector
-> OllamaBrain
-> outputSafetyCheck
-> memory
-> dashboard
```

Dangerous messages still do not enter the model. Unsafe model output is still filtered.

If Ollama is not running, the model is missing, or the local model returns invalid JSON, the app automatically falls back to `MockBrain` instead of crashing.
