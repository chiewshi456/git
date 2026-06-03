from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .ollama_client import OllamaClient


@dataclass
class ModelMemoryDecision:
    items: list[dict]
    reflection: str = ""
    raw: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "reflection": self.reflection,
            "raw": self.raw,
            "error": self.error,
        }


class ModelMemoryWriter:
    """Ask the local model what should be written to long-term memory."""

    ALLOWED_TYPES = {
        "viewer_name",
        "viewer_preference",
        "viewer_dislike",
        "style_rule",
        "conversation_fact",
        "relationship_note",
        "self_improvement",
    }
    SENSITIVE_HINTS = (
        "身份证",
        "手机号",
        "住址",
        "地址",
        "密码",
        "token",
        "api key",
        "银行卡",
        "隐私",
        "自杀",
        "自残",
        "色情",
        "政治",
    )
    MEMORY_SIGNAL_MARKERS = (
        "我叫",
        "你可以叫我",
        "我喜欢",
        "我不喜欢",
        "记住",
        "以后",
        "之后",
        "刚才应该",
        "teach:",
        "教你",
        "短一点",
        "温柔一点",
        "直接一点",
        "多吐槽",
        "少用",
        "不要一直",
        "不够智能",
        "上下文",
        "逻辑",
        "记忆力",
        "没逻辑",
        "答非所问",
    )

    def __init__(self, ollama: OllamaClient) -> None:
        self.ollama = ollama

    def decide(
        self,
        user_input: str,
        ai_reply: str,
        memory_snapshot: dict[str, Any],
        intent: str,
        emotion: str,
    ) -> ModelMemoryDecision:
        prompt = self._build_prompt(
            user_input=user_input,
            ai_reply=ai_reply,
            memory_snapshot=memory_snapshot,
            intent=intent,
            emotion=emotion,
        )
        raw = self.ollama.generate_raw(
            prompt,
            options={
                "temperature": 0.1,
                "top_p": 0.8,
                "num_predict": 220,
            },
            response_format="json",
        )
        if not raw:
            return ModelMemoryDecision(items=[], raw="", error=self.ollama.last_error)

        parsed = self._parse_json(raw)
        if not parsed:
            return ModelMemoryDecision(items=[], raw=raw, error="invalid_json")

        evidence_text = f"{user_input}\n{ai_reply}"
        items = self._sanitize_items(parsed.get("items", []), evidence_text)
        reflection = str(parsed.get("reflection", "")).strip()[:160]
        return ModelMemoryDecision(items=items, reflection=reflection, raw=raw)

    def should_consider(self, user_input: str, intent: str) -> bool:
        if intent in {"teaching", "feedback"}:
            return True
        lowered = user_input.lower()
        return any(marker.lower() in lowered for marker in self.MEMORY_SIGNAL_MARKERS)

    def _build_prompt(
        self,
        user_input: str,
        ai_reply: str,
        memory_snapshot: dict[str, Any],
        intent: str,
        emotion: str,
    ) -> str:
        existing = self._existing_memory_summary(memory_snapshot)
        candidates = self._candidate_summary(user_input)
        return "\n".join(
            [
                "你是 Mika 的长期记忆写入模块。",
                "你的任务不是聊天，而是决定这轮对话有没有值得写入硬盘的长期记忆。",
                "只记录用户明确表达的稳定信息、偏好、纠正、长期风格要求，或者你自己的改进目标。",
                "不要记录敏感隐私、违法、自残、色情、政治争论、医疗金融建议。",
                "不要猜，不要编。没有值得记的内容就返回空 items。",
                "只能输出严格 JSON，不要 markdown，不要解释。",
                "",
                "允许的 type：",
                "viewer_name, viewer_preference, viewer_dislike, style_rule, conversation_fact, relationship_note, self_improvement",
                "",
                "JSON 格式，只能把当前用户明确说过的原文写进 value：",
                '{"items":[{"type":"viewer_name","key":"name","value":"用户明确说出的名字","reason":"用户明确说自己的名字","confidence":0.9}],"reflection":"一句很短的自我反思"}',
                "注意：上面只是格式示例，不是当前记忆内容。不要复制示例里的 value。",
                "",
                f"已有记忆摘要：{existing}",
                f"当前输入候选记忆：{candidates}",
                f"intent={intent}, emotion={emotion}",
                f"用户输入：{user_input}",
                f"Mika 回复：{ai_reply}",
                "",
                "现在输出 JSON：",
            ]
        )

    def _existing_memory_summary(self, memory: dict[str, Any]) -> str:
        profile = memory.get("viewer_profile", {})
        model_memories = memory.get("model_written_memories", [])[-5:]
        parts = []
        name = profile.get("name", "")
        if name:
            parts.append(f"name={name}")
        likes = profile.get("likes", [])
        if likes:
            parts.append("likes=" + "、".join(str(item) for item in likes[-5:]))
        dislikes = profile.get("dislikes", [])
        if dislikes:
            parts.append("dislikes=" + "、".join(str(item) for item in dislikes[-5:]))
        if model_memories:
            parts.append(
                "model_memories="
                + "；".join(str(item.get("value", "")) for item in model_memories)
            )
        return " | ".join(parts) or "暂无"

    def _candidate_summary(self, user_input: str) -> str:
        candidates = []
        name = self._extract_name(user_input)
        if name:
            candidates.append(
                {"type": "viewer_name", "key": "name", "value": name}
            )
        preference = self._extract_preference(user_input)
        if preference:
            candidates.append(
                {"type": "viewer_preference", "key": "likes", "value": preference}
            )
        dislike = self._extract_dislike(user_input)
        if dislike:
            candidates.append(
                {"type": "viewer_dislike", "key": "dislikes", "value": dislike}
            )
        if any(word in user_input for word in ("不够智能", "没逻辑", "答非所问", "太模板")):
            candidates.append(
                {
                    "type": "self_improvement",
                    "key": "context_awareness",
                    "value": "需要增强上下文、自检和追问能力",
                }
            )
        if not candidates:
            return "[]"
        return json.dumps(candidates, ensure_ascii=False)

    def _extract_name(self, text: str) -> str:
        match = re.search(
            r"(?:我叫|你可以叫我)(?!什么|啥|谁|名字)([\u4e00-\u9fffA-Za-z0-9_-]{1,16})",
            text,
        )
        return match.group(1).strip() if match else ""

    def _extract_preference(self, text: str) -> str:
        match = re.search(r"我喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)", text)
        if not match:
            return ""
        return match.group(1).strip()[:40]

    def _extract_dislike(self, text: str) -> str:
        match = re.search(r"我不喜欢(.+?)(?:[，。,.!！?？\s]|$)", text)
        if not match:
            return ""
        return match.group(1).strip()[:40]

    def _parse_json(self, raw: str) -> dict:
        text = raw.strip()
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _sanitize_items(self, raw_items: Any, evidence_text: str) -> list[dict]:
        if not isinstance(raw_items, list):
            return []

        items = []
        for item in raw_items[:5]:
            if not isinstance(item, dict):
                continue
            memory_type = str(item.get("type", "")).strip()
            key = str(item.get("key", "")).strip()[:40]
            value = str(item.get("value", "")).strip()
            reason = str(item.get("reason", "")).strip()[:120]

            if memory_type not in self.ALLOWED_TYPES:
                continue
            if not value or len(value) > 120:
                continue
            if self._looks_sensitive(value) or self._looks_sensitive(key):
                continue
            if not self._has_evidence(memory_type, value, evidence_text):
                continue

            confidence = self._confidence(item.get("confidence"))
            if confidence < 0.55:
                continue

            items.append(
                {
                    "type": memory_type,
                    "key": key or memory_type,
                    "value": value,
                    "reason": reason,
                    "confidence": confidence,
                }
            )
        return items

    def _looks_sensitive(self, text: str) -> bool:
        lowered = text.lower()
        return any(hint.lower() in lowered for hint in self.SENSITIVE_HINTS)

    def _has_evidence(self, memory_type: str, value: str, evidence_text: str) -> bool:
        if memory_type == "self_improvement":
            return True
        normalized_value = self._normalize(value)
        normalized_evidence = self._normalize(evidence_text)
        if normalized_value and normalized_value in normalized_evidence:
            return True

        # Style rules can be paraphrased a little, but still need a visible cue.
        if memory_type == "style_rule":
            cues = ("短", "长", "温柔", "直接", "吐槽", "死板", "智能", "上下文", "口癖")
            return any(cue in value and cue in evidence_text for cue in cues)

        return False

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r"\s+", "", text).lower()

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.7
        return max(0.0, min(1.0, number))
