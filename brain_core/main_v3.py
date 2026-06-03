from __future__ import annotations

import argparse
import sys
from pathlib import Path

from brain_v3 import BrainV3, BrainV3Result


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Mika Brain v3.")
    parser.add_argument("--debug", action="store_true", help="show v3 routing debug")
    parser.add_argument("--llm", choices=("ollama", "off"), default="ollama")
    parser.add_argument("--model", default="qwen2.5:3b", help="Ollama model name, or auto")
    return parser.parse_args()


def print_result(result: BrainV3Result, debug: bool) -> None:
    print(f"\n{result.reply}\n")
    if not debug:
        return
    print("[brain v3 debug]")
    print(f"intent: {result.intent}")
    print(f"route: {result.route}")
    print(f"topic: {result.topic}")
    print(f"model: {result.model}")
    print(f"memory: {result.memory_summary}")
    print()


def main() -> None:
    configure_console_encoding()
    args = parse_args()
    root = Path(__file__).resolve().parent
    brain = BrainV3(root / "data", llm_mode=args.llm, model=args.model)

    print("Mika Brain v3 已启动。")
    print("输入 quit 退出。")
    print("v3: 硬逻辑先行，开放聊天才调用 LLM。")
    print(f"LLM: {args.llm}, model={brain.model_name}")
    print()

    while True:
        try:
            user_input = input("你：")
        except (EOFError, KeyboardInterrupt):
            print("\n我先停。记忆已经写进硬盘。")
            break

        if user_input.strip().lower() == "quit":
            print("好，我先退。下次会继续读 v3 记忆。")
            break

        result = brain.process(user_input)
        print_result(result, args.debug)


if __name__ == "__main__":
    main()
