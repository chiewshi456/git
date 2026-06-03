from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DialogueContext:
    topic: str = ""
    relation: str = "new"
    is_meta_complaint: bool = False
    wants_topic_switch: bool = False
    references_previous: bool = False
    asks_opinion: bool = False
    asks_reason: bool = False
    wants_continuation: bool = False
    last_user_input: str = ""
    last_ai_reply: str = ""
    current_topic: str = ""
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "relation": self.relation,
            "is_meta_complaint": self.is_meta_complaint,
            "wants_topic_switch": self.wants_topic_switch,
            "references_previous": self.references_previous,
            "asks_opinion": self.asks_opinion,
            "asks_reason": self.asks_reason,
            "wants_continuation": self.wants_continuation,
            "last_user_input": self.last_user_input,
            "last_ai_reply": self.last_ai_reply,
            "current_topic": self.current_topic,
            "summary": self.summary,
        }


class ContextAnalyzer:
    """Lightweight dialogue context for short local conversations."""

    TOPIC_KEYWORDS = {
        "food": ("吃", "火锅", "外卖", "奶茶", "饿", "宵夜", "饭"),
        "work": ("工作", "上班", "加班", "老板", "同事", "下班", "累"),
        "game": ("游戏", "开黑", "排位", "通关", "手柄"),
        "tech": ("代码", "bug", "报错", "模型", "AI", "llm", "ollama", "程序"),
        "emotion": ("难过", "开心", "焦虑", "紧张", "压力", "不舒服"),
        "brain": ("智能", "逻辑", "对话", "学习", "记忆", "成长", "脑"),
        "music": ("音乐", "唱歌", "听歌", "歌单"),
    }
    META_COMPLAINTS = (
        "不够智能",
        "不聪明",
        "没逻辑",
        "没有逻辑",
        "不能对话",
        "不像ai",
        "像模板",
        "太模板",
        "太规则",
        "机械",
        "死板",
        "没脑子",
        "答非所问",
        "上下文差",
        "上下文理解能力很差",
        "理解能力很差",
        "逻辑能力很差",
        "逻辑差",
        "没有记忆力",
        "记忆力很差",
        "记忆力差",
    )
    TOPIC_SWITCHES = (
        "换个话题",
        "换一个话题",
        "换话题",
        "别聊这个",
        "不聊这个",
        "先不说这个",
        "说点别的",
    )
    PREVIOUS_REFERENCES = (
        "刚才",
        "刚刚",
        "上一句",
        "上面",
        "这个",
        "那个",
        "这句",
        "那句",
        "你说的",
        "这么说",
        "这样说",
        "为什么这样",
        "为什么这么",
        "继续",
        "接着",
        "然后呢",
        "什么意思",
    )

    def analyze(self, user_input: str, intent: str, memory: dict) -> dict:
        text = user_input.strip()
        lowered = text.lower()
        conversation = memory.get("conversation_context", {})
        last_user = str(conversation.get("last_user_input", ""))
        last_reply = str(conversation.get("last_ai_reply", ""))
        current_topic = str(conversation.get("current_topic", ""))

        references_previous = any(marker in text for marker in self.PREVIOUS_REFERENCES)
        asks_reason = "为什么" in text or lowered.startswith("why")
        wants_continuation = any(marker in text for marker in ("继续", "接着", "然后呢", "展开"))
        asks_opinion = any(marker in text for marker in ("怎么样", "觉得", "怎么看", "你说呢"))
        is_meta_complaint = any(marker in lowered for marker in self.META_COMPLAINTS)
        wants_topic_switch = any(marker in text for marker in self.TOPIC_SWITCHES)

        detected_topic = self._detect_topic(text)
        if wants_topic_switch:
            topic = ""
        elif detected_topic:
            topic = detected_topic
        elif references_previous or wants_continuation or asks_reason:
            topic = current_topic
        else:
            topic = ""

        relation = "new"
        if wants_topic_switch:
            relation = "topic_switch"
        elif references_previous or (asks_reason and last_user):
            relation = "follow_up"
        elif topic and current_topic and topic == current_topic:
            relation = "same_topic"
        elif wants_continuation:
            relation = "continue"
        elif intent in {"question", "normal"} and last_user:
            relation = "possibly_related"

        summary = self._summary(
            topic=topic,
            relation=relation,
            is_meta_complaint=is_meta_complaint,
            last_user=last_user,
            last_reply=last_reply,
        )
        return DialogueContext(
            topic=topic,
            relation=relation,
            is_meta_complaint=is_meta_complaint,
            wants_topic_switch=wants_topic_switch,
            references_previous=references_previous,
            asks_opinion=asks_opinion,
            asks_reason=asks_reason,
            wants_continuation=wants_continuation,
            last_user_input=last_user,
            last_ai_reply=last_reply,
            current_topic=current_topic,
            summary=summary,
        ).to_dict()

    def _detect_topic(self, text: str) -> str:
        lowered = text.lower()
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                target = lowered if keyword.isascii() else text
                if keyword.lower() in target:
                    return topic
        return ""

    @staticmethod
    def _summary(
        topic: str,
        relation: str,
        is_meta_complaint: bool,
        last_user: str,
        last_reply: str,
    ) -> str:
        parts = [f"relation={relation}"]
        if topic:
            parts.append(f"topic={topic}")
        if is_meta_complaint:
            parts.append("user_is_complaining_about_intelligence")
        if last_user:
            parts.append(f"last_user={last_user[:40]}")
        if last_reply:
            parts.append(f"last_ai={last_reply[:40]}")
        return "; ".join(parts)
