from __future__ import annotations

import argparse
import sys
from pathlib import Path

from brain_v2.core import BrainV2Core, BrainV2Response


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Brain v2.")
    parser.add_argument("--debug", action="store_true", help="show structured brain debug")
    parser.add_argument(
        "--llm",
        choices=("ollama", "off"),
        default="ollama",
        help="use local Ollama or deterministic fallback only",
    )
    parser.add_argument(
        "--ollama-model",
        default="auto",
        help="chat model name, or auto to prefer qwen2.5 then fallback",
    )
    parser.add_argument(
        "--memory-model",
        default="auto",
        help="reasoning/memory model name, or auto to prefer qwen2.5 then fallback",
    )
    return parser.parse_args()


def print_response(response: BrainV2Response, debug: bool) -> None:
    print(f"\n{response.reply}\n")
    if not debug:
        return
    print("[brain v2 debug]")
    print(f"reply_source: {response.reply_source}")
    print(f"critic: {response.critic_summary}")
    print(f"understanding: {response.understanding}")
    print(f"policy: {response.policy}")
    print(f"retrieved_memory: {response.retrieved_memory}")
    print(f"memory: {response.memory_summary}")
    print(f"model_memory: {response.model_memory_summary}")
    print()


def main() -> None:
    configure_console_encoding()
    args = parse_args()
    root = Path(__file__).resolve().parent
    brain = BrainV2Core(
        root / "data",
        llm_mode=args.llm,
        ollama_model=args.ollama_model,
        memory_model=args.memory_model,
    )

    print("Mika Brain v2 已启动。")
    print("输入 quit 退出。")
    print("v2: 先理解 JSON，再按策略回复。")
    print(
        "LLM: "
        f"{args.llm}, chat={brain.chat_model_name}, reasoning={brain.memory_model_name}, "
        f"selection={brain.model_selection_note}"
    )
    print()

    while True:
        try:
            user_input = input("你：")
        except (EOFError, KeyboardInterrupt):
            print("\n先暂停，我把上下文留在硬盘里。")
            break

        if user_input.strip().lower() == "quit":
            print("好，我先退出。下次打开还会读 memory.json。")
            break

        response = brain.process(user_input)
        print_response(response, args.debug)


if __name__ == "__main__":
    main()
