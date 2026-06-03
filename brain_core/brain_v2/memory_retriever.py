from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievedMemory:
    facts: list[str] = field(default_factory=list)
    preferences: list[str] = field(default_factory=list)
    style_rules: list[str] = field(default_factory=list)
    recent_context: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "facts": self.facts,
            "preferences": self.preferences,
            "style_rules": self.style_rules,
            "recent_context": self.recent_context,
        }

    def summary(self) -> str:
        chunks = []
        if self.facts:
            chunks.append("facts=" + "；".join(self.facts))
        if self.preferences:
            chunks.append("prefs=" + "；".join(self.preferences))
        if self.style_rules:
            chunks.append("rules=" + "；".join(self.style_rules))
        if self.recent_context:
            chunks.append("recent=" + "；".join(self.recent_context))
        return " | ".join(chunks) or "无相关记忆"


class MemoryRetriever:
    def retrieve(self, memory: dict[str, Any], understanding: dict[str, Any]) -> RetrievedMemory:
        profile = memory.get("viewer_profile", {})
        teaching = memory.get("teaching", {})
        conversation = memory.get("conversation_context", {})
        model_memories = memory.get("model_written_memories", [])

        facts: list[str] = []
        preferences: list[str] = []
        style_rules: list[str] = []
        recent_context: list[str] = []

        name = profile.get("name", "")
        if name:
            facts.append(f"用户名字={name}")

        for like in profile.get("likes", [])[-5:]:
            preferences.append(f"喜欢={like}")
        for dislike in profile.get("dislikes", [])[-5:]:
            preferences.append(f"不喜欢={dislike}")

        for item in model_memories[-8:]:
            memory_type = item.get("type", "")
            value = item.get("value", "")
            if not value:
                continue
            if memory_type == "viewer_name":
                facts.append(f"用户名字={value}")
            elif memory_type == "viewer_preference":
                preferences.append(f"喜欢={value}")
            elif memory_type == "viewer_dislike":
                preferences.append(f"不喜欢={value}")
            elif memory_type in {"style_rule", "self_improvement"}:
                style_rules.append(str(value))

        for rule in teaching.get("rules", [])[-5:]:
            value = rule.get("rule", "")
            if value:
                style_rules.append(str(value))

        last_user = conversation.get("last_user_input", "")
        last_ai = conversation.get("last_ai_reply", "")
        if last_user:
            recent_context.append(f"上一轮用户={last_user}")
        if last_ai:
            recent_context.append(f"上一轮Mika={last_ai}")

        # Deduplicate while preserving order.
        return RetrievedMemory(
            facts=self._unique(facts, 8),
            preferences=self._unique(preferences, 8),
            style_rules=self._unique(style_rules, 8),
            recent_context=self._unique(recent_context, 4),
        )

    @staticmethod
    def _unique(values: list[str], limit: int) -> list[str]:
        seen = set()
        result = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            result.append(value)
        return result[-limit:]
