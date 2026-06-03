from __future__ import annotations

import argparse
import sys
from pathlib import Path

from brain.core import BrainCore, BrainResponse


def configure_console_encoding() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def format_drives(drives: list[dict]) -> str:
    return ", ".join(drive["name"] for drive in drives)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local AI brain core.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show intent, emotion, drives, state, and memory after each reply",
    )
    parser.add_argument(
        "--llm",
        choices=("auto", "off", "ollama"),
        default="auto",
        help="use local Ollama for slower open-ended replies; auto falls back to fast brain",
    )
    parser.add_argument(
        "--ollama-model",
        default="mika-ai:0.1",
        help="Ollama model name used when --llm is auto or ollama",
    )
    parser.add_argument(
        "--memory-model",
        default="llama3.2:3b",
        help="Ollama model used for structured model-written memory",
    )
    return parser.parse_args()


def print_response(response: BrainResponse, debug: bool = False) -> None:
    print(f"\n{response.final_reply}\n")
    if not debug:
        return

    print("[brain debug]")
    print(f"intent: {response.intent}")
    print(f"emotion: {response.emotion}")
    print(f"attention: {response.attention_target}")
    print(f"reply_intent: {response.reply_intent}")
    print(f"reply_source: {response.reply_source}")
    print(f"drives: {format_drives(response.drives)}")
    print(f"state: {response.state_summary}")
    print(f"memory: {response.memory_summary}")
    if response.context_summary:
        print(f"context: {response.context_summary}")
    if response.model_memory_summary:
        print(f"model_memory: {response.model_memory_summary}")
    print(f"learning: {response.learning_summary}")
    print(f"growth: {response.growth_summary}")
    print(f"training: {response.training_summary}")
    if response.teaching_summary:
        print(f"teaching: {response.teaching_summary}")
    print()


def main() -> None:
    configure_console_encoding()
    args = parse_args()

    project_root = Path(__file__).resolve().parent
    brain = BrainCore(
        project_root / "data",
        llm_mode=args.llm,
        ollama_model=args.ollama_model,
        memory_model=args.memory_model,
    )

    print("AI Brain Core v0.6 已启动。")
    print("输入 quit 退出。")
    print("直接按 Enter 代表安静输入。")
    print(f"LLM: {args.llm} ({args.ollama_model})")
    print(f"Memory writer model: {args.memory_model}")
    print()

    while True:
        try:
            user_input = input("你：")
        except (EOFError, KeyboardInterrupt):
            print("\n对话先暂停，我的核心还在。")
            break

        if user_input.strip().lower() == "quit":
            print("那我先退出啦。下次记得继续测试我，好不好。")
            break

        response = brain.process(user_input)
        print_response(response, debug=args.debug)


if __name__ == "__main__":
    main()
