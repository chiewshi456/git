from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class FeedbackResult:
    is_feedback: bool = False
    sentiment: str = "neutral"
    style_updates: dict = field(default_factory=dict)
    rule: str = ""
    note: str = ""
    matched: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_feedback": self.is_feedback,
            "sentiment": self.sentiment,
            "style_updates": self.style_updates,
            "rule": self.rule,
            "note": self.note,
            "matched": self.matched,
        }


class FeedbackInterpreter:
    """Parse direct user feedback into durable style controls."""

    POSITIVE_MARKERS = (
        "这句不错",
        "这句可以",
        "这句好",
        "这样可以",
        "这样好",
        "这个可以",
        "自然一点了",
        "这句自然",
        "有感觉",
        "像她了",
        "像了",
        "好一点",
        "可以保持",
        "保持这样",
    )
    NEGATIVE_MARKERS = (
        "这句不行",
        "不太行",
        "太死板",
        "死板",
        "不够智能",
        "不聪明",
        "太像客服",
        "像客服",
        "不像直播",
        "不像她",
        "没逻辑",
        "答非所问",
        "太尬",
        "很尬",
        "机械",
        "生硬",
        "复读",
        "上下文差",
        "上下文理解能力很差",
        "理解能力很差",
        "逻辑能力很差",
        "逻辑差",
        "没有记忆力",
        "记忆力差",
        "记忆力很差",
    )
    INTELLIGENCE_MARKERS = (
        "不够智能",
        "不聪明",
        "没逻辑",
        "不能对话",
        "答非所问",
        "像模板",
        "太规则",
        "上下文差",
        "上下文理解能力很差",
        "理解能力很差",
        "逻辑能力很差",
        "逻辑差",
        "没有记忆力",
        "记忆力差",
        "记忆力很差",
    )
    CONTEXT_MARKERS = (
        "上下文差",
        "上下文理解能力很差",
        "理解能力很差",
        "不能对话",
        "答非所问",
    )
    LOGIC_MARKERS = (
        "逻辑能力很差",
        "逻辑差",
        "没逻辑",
        "没有逻辑",
    )
    MEMORY_MARKERS = (
        "没有记忆力",
        "又没有记忆力",
        "记忆力差",
        "记忆力很差",
    )
    SHORT_MARKERS = (
        "短一点",
        "简短一点",
        "回答短",
        "回复短",
        "别废话",
        "少废话",
        "别讲太长",
        "不要太长",
        "压短",
    )
    DETAILED_MARKERS = (
        "多说一点",
        "详细一点",
        "展开一点",
        "认真讲",
        "讲清楚一点",
    )
    PLAYFUL_MARKERS = (
        "多吐槽一点",
        "吐槽多一点",
        "嘴硬一点",
        "调皮一点",
        "机灵一点",
        "接梗",
        "反打",
    )
    CARING_MARKERS = (
        "温柔一点",
        "认真一点",
        "别太凶",
        "柔和一点",
        "安慰一点",
    )
    DIRECT_MARKERS = (
        "直接一点",
        "别绕",
        "少解释",
        "先回答",
        "别铺垫",
    )
    AVOID_PHRASE_PATTERNS = (
        ("欸", ("少用欸", "别一直欸", "不要一直欸", "别老欸")),
        ("CPU", ("不要一直说cpu", "别一直说cpu", "少说cpu", "少用cpu", "别老cpu")),
        ("好不好", ("少用好不好", "别一直好不好", "不要一直好不好")),
        ("啦", ("少用啦", "别一直啦", "不要一直啦")),
        ("主人", ("别叫我主人", "不要叫我主人")),
    )

    def parse(self, text: str) -> FeedbackResult:
        raw = text.strip()
        lowered = raw.lower()
        matched: list[str] = []
        style_updates: dict = {}

        sentiment = "neutral"
        if self._has_any(raw, self.NEGATIVE_MARKERS):
            sentiment = "negative"
            matched.append("negative")
        elif self._has_any(raw, self.POSITIVE_MARKERS):
            sentiment = "positive"
            matched.append("positive")

        length = self._detect_length(raw)
        if length:
            style_updates["length"] = length
            matched.append(f"length:{length}")

        tone = self._detect_tone(raw)
        if tone:
            style_updates["tone"] = tone
            matched.append(f"tone:{tone}")

        if self._has_any(raw, self.INTELLIGENCE_MARKERS):
            if sentiment == "neutral":
                sentiment = "negative"
            style_updates["needs_context"] = True
            matched.append("capability:context")
        if self._has_any(raw, self.LOGIC_MARKERS):
            if sentiment == "neutral":
                sentiment = "negative"
            style_updates["needs_logic"] = True
            matched.append("capability:logic")
        if self._has_any(raw, self.MEMORY_MARKERS):
            if sentiment == "neutral":
                sentiment = "negative"
            style_updates["needs_memory"] = True
            matched.append("capability:memory")

        avoid_phrases = self._detect_avoid_phrases(lowered)
        if avoid_phrases:
            style_updates["avoid_phrases"] = avoid_phrases
            matched.append("avoid:" + ",".join(avoid_phrases))

        rule = self._extract_rule(raw)
        if rule:
            matched.append("rule")

        is_feedback = bool(matched)
        note = self._make_note(sentiment, style_updates, rule) if is_feedback else ""
        return FeedbackResult(
            is_feedback=is_feedback,
            sentiment=sentiment,
            style_updates=style_updates,
            rule=rule,
            note=note,
            matched=matched,
        )

    def reply_for(self, result: dict) -> str:
        style_updates = result.get("style_updates", {})
        avoid_phrases = style_updates.get("avoid_phrases", [])
        length = style_updates.get("length", "")
        tone = style_updates.get("tone", "")

        if avoid_phrases:
            joined = "、".join(avoid_phrases)
            return f"收到，我会少用{joined}。同一个梗一直用，确实会有点不对劲。"
        if length == "short":
            return "收到，之后我会压短一点。先接住重点，不把话说成说明书。"
        if length == "detailed":
            return "收到，遇到需要解释的地方我会多讲一点，但还是尽量别拖太长。"
        if tone == "playful":
            return "收到，多一点吐槽和反打。先声明，我嘴硬但不会乱攻击你。"
        if tone == "caring":
            return "收到，我会放柔一点。不是装温柔，是把反应调得更像在认真听。"
        if tone == "direct":
            return "收到，我会更直接一点。少绕路，先回答重点。"
        if style_updates.get("needs_memory"):
            return "对，刚才记忆这块接得很差。我不该一直反问你是不是在测试，而是先说清楚我记得什么、不记得什么。"
        if style_updates.get("needs_logic"):
            return "对，刚才逻辑不稳。我会先判断你的真实意图，再决定要不要接旧话题，不再硬套模板。"
        if style_updates.get("needs_context"):
            return "对，刚才上下文接错了。我把旧话题硬粘到新问题上，之后会先判断你是不是已经换题。"
        if result.get("rule"):
            return "收到，这条规则我记下来了。之后我会照这个方向试。"
        if result.get("sentiment") == "positive":
            return "收到，这句我先存成好样本。等一下，我好像真的学到一点。"
        if result.get("sentiment") == "negative":
            return "收到，刚刚那种味道我记成反例。下一句我会调自然一点。"
        return "收到，这条反馈我记下来了。我的对话习惯会慢慢往这边调。"

    def _detect_length(self, text: str) -> str:
        if self._has_any(text, self.SHORT_MARKERS):
            return "short"
        if self._has_any(text, self.DETAILED_MARKERS):
            return "detailed"
        return ""

    def _detect_tone(self, text: str) -> str:
        if self._has_any(text, self.PLAYFUL_MARKERS):
            return "playful"
        if self._has_any(text, self.CARING_MARKERS):
            return "caring"
        if self._has_any(text, self.DIRECT_MARKERS):
            return "direct"
        return ""

    def _detect_avoid_phrases(self, lowered_text: str) -> list[str]:
        phrases = []
        for phrase, patterns in self.AVOID_PHRASE_PATTERNS:
            if any(pattern in lowered_text for pattern in patterns):
                phrases.append(phrase)
        return phrases

    def _extract_rule(self, text: str) -> str:
        patterns = (
            r"(以后(?:不要|别|少|尽量|应该).{2,60})",
            r"(之后(?:不要|别|少|尽量|应该).{2,60})",
            r"(刚才应该.{2,60})",
            r"(你应该.{2,60})",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip(" ，。,.!！?？")
        return ""

    def _make_note(self, sentiment: str, style_updates: dict, rule: str) -> str:
        parts = []
        if sentiment != "neutral":
            parts.append(f"{sentiment}反馈")
        if style_updates.get("length"):
            parts.append(f"长度偏好={style_updates['length']}")
        if style_updates.get("tone"):
            parts.append(f"语气偏好={style_updates['tone']}")
        if style_updates.get("avoid_phrases"):
            parts.append("少用=" + "、".join(style_updates["avoid_phrases"]))
        if style_updates.get("needs_context"):
            parts.append("需要增强上下文和自检")
        if style_updates.get("needs_logic"):
            parts.append("需要增强逻辑判断")
        if style_updates.get("needs_memory"):
            parts.append("需要增强记忆解释")
        if rule:
            parts.append(f"规则={rule}")
        return "；".join(parts)

    @staticmethod
    def _has_any(text: str, markers: tuple[str, ...]) -> bool:
        return any(marker in text for marker in markers)
