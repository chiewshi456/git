from __future__ import annotations

from typing import Any

from brain.ollama_client import OllamaClient

from .soul import SoulProfile


class Responder:
    def __init__(self, ollama: OllamaClient, soul: SoulProfile | None = None) -> None:
        self.ollama = ollama
        self.soul = soul or SoulProfile()

    def respond(
        self,
        user_input: str,
        understanding: dict[str, Any],
        retrieved_memory: dict[str, Any],
        policy: dict[str, Any],
    ) -> tuple[str, str]:
        deterministic = policy.get("deterministic_reply", "")
        if policy.get("mode") == "deterministic" and deterministic:
            return deterministic, "policy"

        prompt = self._build_prompt(user_input, understanding, retrieved_memory, policy)
        raw = self.ollama.generate_raw(
            prompt,
            options={"temperature": 0.55, "top_p": 0.86, "num_predict": 120},
        )
        reply = self._clean(raw)
        if not reply:
            reply = "等一下，我这句没接稳。你再给我一点上下文，我重新回答。"
            return reply, "fallback"
        return reply, f"ollama:{self.ollama.config.model}"

    def _build_prompt(
        self,
        user_input: str,
        understanding: dict[str, Any],
        retrieved_memory: dict[str, Any],
        policy: dict[str, Any],
    ) -> str:
        return "\n".join(
            [
                self.soul.prompt_block(),
                "",
                "理解结果 JSON：",
                str(understanding),
                "",
                "相关记忆：",
                str(retrieved_memory),
                "",
                "回复策略：",
                str(policy),
                "",
                f"用户当前输入：{user_input}",
                "",
                "现在用 Mika 口吻回复。",
                "只输出要说的话，1到2句，直接接住当前输入。",
            ]
        )

    @staticmethod
    def _clean(text: str) -> str:
        cleaned = str(text).strip().strip('"“”')
        for prefix in ("Mika:", "Mika：", "主播:", "主播：", "AI:", "AI："):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        cleaned = cleaned.replace("\r", " ").replace("\n", " ")
        while "  " in cleaned:
            cleaned = cleaned.replace("  ", " ")
        return cleaned[:180].strip()
