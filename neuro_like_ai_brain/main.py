from __future__ import annotations

import os
import sys
from pathlib import Path

from brain.core import NeuroLikeBrain
from providers.fake_provider import FakeAIProvider
from providers.ollama_provider import OllamaProvider
from providers.openai_provider import OpenAIProvider


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def create_provider():
    provider_name = os.getenv("NEURO_BRAIN_PROVIDER", "fake").strip().lower()

    if provider_name == "fake":
        return FakeAIProvider()
    if provider_name == "ollama":
        return OllamaProvider()
    if provider_name == "openai":
        return OpenAIProvider()

    print(f"未知 provider: {provider_name}，已回退到 fake_provider。")
    return FakeAIProvider()


def print_result(result: dict) -> None:
    print(f"\n主播：{result['reply']}\n")
    print("[debug]")
    print(f"intent: {result['intent']}")
    print(f"emotion: {result['emotion']}")
    print(f"state: {result['state_summary']}")
    print(f"memory: {result['memory_summary']}")
    print()


def main() -> None:
    configure_console_encoding()

    project_root = Path(__file__).resolve().parent
    data_dir = Path(os.getenv("NEURO_BRAIN_DATA_DIR", project_root / "data"))

    brain = NeuroLikeBrain(
        data_dir=data_dir,
        provider=create_provider(),
    )

    print("Neuro-like AI Brain v0.1 已启动。")
    print("输入 quit 退出。")
    print("直接按 Enter 代表聊天室安静。")
    print()

    while True:
        try:
            user_text = input("你：")
        except (EOFError, KeyboardInterrupt):
            print("\n直播中断，主播先下播了。")
            break

        if user_text.strip().lower() == "quit":
            print("主播：那我先下播啦。别把我从记忆里卸载掉。")
            break

        if not user_text.strip():
            result = brain.autonomous_tick()
        else:
            result = brain.process_input(user_text)

        print_result(result)


if __name__ == "__main__":
    main()
