from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


PREFERRED_OLLAMA_MODELS = (
    "qwen2.5:7b",
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "mika-ai:0.1",
    "llama3.2:3b",
)


@dataclass(frozen=True)
class ModelSelection:
    chat_model: str
    memory_model: str
    available_models: tuple[str, ...]
    note: str


def list_ollama_models(endpoint: str = "http://127.0.0.1:11434", timeout_seconds: float = 3.0) -> tuple[str, ...]:
    try:
        request = urllib.request.Request(f"{endpoint.rstrip('/')}/api/tags", method="GET")
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError, json.JSONDecodeError):
        return ()

    models = data.get("models", [])
    if not isinstance(models, list):
        return ()
    names = [str(item.get("name", "")).strip() for item in models if isinstance(item, dict)]
    return tuple(name for name in names if name)


def resolve_ollama_models(
    requested_chat_model: str,
    requested_memory_model: str,
    endpoint: str = "http://127.0.0.1:11434",
) -> ModelSelection:
    available = list_ollama_models(endpoint)

    chat_model, chat_note = _resolve_one(requested_chat_model, available)
    memory_model, memory_note = _resolve_one(requested_memory_model, available)

    notes = [note for note in (chat_note, memory_note) if note]
    return ModelSelection(
        chat_model=chat_model,
        memory_model=memory_model,
        available_models=available,
        note="; ".join(notes) or "explicit",
    )


def _resolve_one(requested: str, available: tuple[str, ...]) -> tuple[str, str]:
    requested = (requested or "auto").strip()
    if requested != "auto":
        return requested, ""

    for model in PREFERRED_OLLAMA_MODELS:
        if model in available:
            return model, f"auto->{model}"

    # Keep a stable fallback even if Ollama is offline during startup.
    return "mika-ai:0.1", "auto->mika-ai:0.1(no_tags)"
