from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from brain_v3 import BrainV3


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process one Mika Brain v3 JSON request.")
    parser.add_argument("--llm", choices=("ollama", "off"), default="off")
    parser.add_argument("--model", default="qwen2.5:3b")
    return parser.parse_args()


def read_request() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("request must be a JSON object")
    return data


def selected_text(request: dict[str, Any]) -> str:
    text = request.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    selected = request.get("selectedMessage")
    if isinstance(selected, dict):
        message_text = selected.get("text")
        if isinstance(message_text, str):
            return message_text.strip()

    return ""


def main() -> int:
    configure_console_encoding()
    args = parse_args()
    root = Path(__file__).resolve().parent

    try:
        request = read_request()
        user_text = selected_text(request)
        if not user_text:
            raise ValueError("missing text")

        brain = BrainV3(root / "data", llm_mode=args.llm, model=args.model)
        result = brain.process(user_text)
        payload = {
            "ok": True,
            "reply": result.reply,
            "intent": result.intent,
            "route": result.route,
            "topic": result.topic,
            "model": result.model,
            "memorySummary": result.memory_summary,
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 0
    except Exception as exc:
        payload = {
            "ok": False,
            "error": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
