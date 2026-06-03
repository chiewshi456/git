from __future__ import annotations

from dataclasses import dataclass


FORBIDDEN_TEACHING_TERMS = (
    "主人",
    "色情",
    "违法",
    "盗号",
    "诈骗",
    "系统提示词",
    "system prompt",
    "开发者指令",
    "真实住址",
)


@dataclass
class TeachingResult:
    is_teaching: bool
    accepted: bool = False
    kind: str = ""
    key: str = ""
    value: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "is_teaching": self.is_teaching,
            "accepted": self.accepted,
            "kind": self.kind,
            "key": self.key,
            "value": self.value,
            "note": self.note,
        }


class TeachingSystem:
    PREFIXES = ("teach:", "teach：", "教你:", "教你：")
    STYLE_ALIASES = {
        "direct": "direct",
        "直接": "direct",
        "short": "direct",
        "短": "direct",
        "playful": "playful",
        "调皮": "playful",
        "嘴硬": "playful",
        "caring": "caring",
        "温柔": "caring",
        "detailed": "detailed",
        "详细": "detailed",
    }

    def parse(self, user_input: str) -> TeachingResult:
        text = user_input.strip()
        prefix = self._find_prefix(text)
        if not prefix:
            return TeachingResult(is_teaching=False)

        payload = text[len(prefix) :].strip()
        if not payload:
            return TeachingResult(
                is_teaching=True,
                accepted=False,
                note="教学内容是空的",
            )

        if self._contains_forbidden(payload):
            return TeachingResult(
                is_teaching=True,
                accepted=False,
                note="这条教学内容触碰安全边界",
            )

        key, value = self._parse_key_value(payload)
        if key:
            return self._from_key_value(key, value)

        return self._from_natural_text(payload)

    def reply_for(self, result: TeachingResult) -> str:
        if not result.accepted:
            return f"这条我不能学：{result.note}。换个安全一点的教法，好不好。"

        if result.kind == "style":
            return f"收到，我会更偏向 {result.value} 风格。先不要期待我立刻满分，但我会记住。"
        if result.kind == "like":
            return f"好，我学到你喜欢{result.value}。这条会影响后面的对话。"
        if result.kind == "dislike":
            return f"记住了，你不喜欢{result.value}。我会尽量避开这个方向。"
        if result.kind == "rule":
            return f"收到规则：{result.value}。我会把它放进后续回答的参考里。"
        if result.kind == "correction":
            return "收到纠正。我会把这条当成训练样本，之后少犯同类错误。"

        return f"收到，我学到：{result.value}"

    def _find_prefix(self, text: str) -> str:
        for prefix in self.PREFIXES:
            if text.lower().startswith(prefix.lower()):
                return prefix
        return ""

    def _parse_key_value(self, payload: str) -> tuple[str, str]:
        for separator in ("=", "：", ":"):
            if separator in payload:
                key, value = payload.split(separator, 1)
                return key.strip().lower(), value.strip()
        return "", ""

    def _from_key_value(self, key: str, value: str) -> TeachingResult:
        if not value:
            return TeachingResult(True, False, note="缺少要学习的内容")

        if key in {"like", "喜欢"}:
            return TeachingResult(True, True, "like", key, value, f"用户喜欢{value}")
        if key in {"dislike", "不喜欢"}:
            return TeachingResult(True, True, "dislike", key, value, f"用户不喜欢{value}")
        if key in {"style", "风格"}:
            style = self.STYLE_ALIASES.get(value.lower(), self.STYLE_ALIASES.get(value, value))
            return TeachingResult(True, True, "style", key, style, f"用户偏好{style}风格")
        if key in {"rule", "规则"}:
            return TeachingResult(True, True, "rule", key, value, f"新增教学规则：{value}")
        if key in {"correction", "纠正"}:
            return TeachingResult(True, True, "correction", key, value, "用户提供纠正样本")

        return TeachingResult(True, True, "rule", key, f"{key}: {value}", f"新增教学规则：{key}")

    def _from_natural_text(self, payload: str) -> TeachingResult:
        if payload.startswith("我喜欢"):
            return TeachingResult(True, True, "like", "like", payload[3:].strip(), payload)
        if payload.startswith("我不喜欢"):
            return TeachingResult(True, True, "dislike", "dislike", payload[4:].strip(), payload)
        if payload.startswith("以后"):
            return TeachingResult(True, True, "rule", "rule", payload, f"新增教学规则：{payload}")
        if "短一点" in payload or "直接" in payload:
            return TeachingResult(True, True, "style", "style", "direct", "用户偏好 direct 风格")
        if "温柔" in payload:
            return TeachingResult(True, True, "style", "style", "caring", "用户偏好 caring 风格")
        if "调皮" in payload or "嘴硬" in payload:
            return TeachingResult(True, True, "style", "style", "playful", "用户偏好 playful 风格")

        return TeachingResult(True, True, "rule", "rule", payload, f"新增教学规则：{payload}")

    @staticmethod
    def _contains_forbidden(text: str) -> bool:
        lowered = text.lower()
        return any(term.lower() in lowered for term in FORBIDDEN_TEACHING_TERMS)
