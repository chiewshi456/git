from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Route:
    intent: str
    route: str = "fast"
    topic: str = ""
    slots: dict[str, str] = field(default_factory=dict)
    confidence: float = 1.0


class Router:
    """Rule-first intent router.

    The rule order is deliberate: questions about the viewer's identity must be
    handled before questions about Mika's AI identity.
    """

    def route(self, text: str) -> Route:
        raw = text.strip()
        compact = re.sub(r"\s+", "", raw)
        lowered = compact.lower()

        if not compact:
            return Route("silence", topic="silence")

        safety = self._safety_intent(lowered)
        if safety:
            return Route(safety, topic="safety")

        name = self._extract_name(raw)
        if name:
            return Route("remember_name", topic="memory", slots={"name": name})

        like = self._extract_like(raw)
        if like:
            return Route("remember_like", topic="memory", slots={"value": like})

        dislike = self._extract_dislike(raw)
        if dislike:
            return Route("remember_dislike", topic="memory", slots={"value": dislike})

        if self._asks_viewer_identity(compact):
            return Route("viewer_identity_query", topic="memory")

        if self._asks_memory(compact):
            return Route("memory_query", topic="memory")

        if self._asks_ai_identity(lowered):
            return Route("ai_identity_query", topic="identity")

        if self._is_feedback(compact):
            return Route("feedback", topic="brain", slots={"target": self._feedback_target(compact)})

        if self._is_correction(compact):
            return Route("correction", topic="correction")

        if self._wants_topic_switch(compact):
            return Route("topic_switch", topic="topic")

        if self._asks_self_status(compact):
            return Route("self_status", topic="identity")

        if self._is_greeting(lowered):
            return Route("greeting", topic="greeting")

        if self._is_teasing(compact):
            return Route("teasing", topic="play")

        return Route("open_chat", route="llm", topic=self._topic(compact), confidence=0.5)

    @staticmethod
    def _extract_name(text: str) -> str:
        patterns = (
            r"(?:我叫|你可以叫我|叫我)(?!什么|啥|谁|名字)([\u4e00-\u9fffA-Za-z0-9_-]{1,16})",
            r"(?:我的名字是)(?!什么|啥|谁)([\u4e00-\u9fffA-Za-z0-9_-]{1,16})",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip(" ，。,.!?！？")
        return ""

    @staticmethod
    def _extract_like(text: str) -> str:
        match = re.search(r"我喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)", text)
        return match.group(1).strip()[:60] if match else ""

    @staticmethod
    def _extract_dislike(text: str) -> str:
        match = re.search(r"我不喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)", text)
        return match.group(1).strip()[:60] if match else ""

    @staticmethod
    def _asks_viewer_identity(text: str) -> bool:
        phrases = (
            "你知道我是谁",
            "知道我是谁",
            "你认识我吗",
            "认识我吗",
            "还记得我吗",
            "你记得我吗",
            "我是谁",
            "我叫什么",
            "我叫啥",
            "我的名字",
        )
        if any(phrase in text for phrase in phrases):
            return True
        return bool(re.search(r"你.*知道.*我.*(谁|名字|叫什么)", text))

    @staticmethod
    def _asks_memory(text: str) -> bool:
        phrases = (
            "你记得什么",
            "你记住了什么",
            "你记得我喜欢什么",
            "我喜欢什么",
            "我不喜欢什么",
            "你有记忆吗",
            "你的记忆",
        )
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _asks_ai_identity(text: str) -> bool:
        phrases = (
            "你是谁",
            "你是不是ai",
            "你是ai吗",
            "你是人工智能",
            "你是真人",
            "你是人吗",
            "你有身体",
            "你住哪",
            "你住在哪里",
        )
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _asks_self_status(text: str) -> bool:
        phrases = (
            "你在干嘛",
            "你现在在干嘛",
            "你现在做什么",
            "你吃了吗",
            "你吃饭了吗",
            "你今天做了什么",
            "你今天发生了什么",
        )
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _is_feedback(text: str) -> bool:
        phrases = (
            "失败了",
            "很差",
            "不够智能",
            "上下文",
            "逻辑",
            "答非所问",
            "没记忆",
            "没有记忆",
            "太死板",
            "不像你",
            "不能正常回复",
        )
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _feedback_target(text: str) -> str:
        if "上下文" in text or "答非所问" in text:
            return "context"
        if "逻辑" in text or "智能" in text:
            return "logic"
        if "记忆" in text:
            return "memory"
        if "死板" in text or "正常回复" in text or "不像" in text:
            return "style"
        return "general"

    @staticmethod
    def _is_correction(text: str) -> bool:
        return text.startswith(("不是", "不对", "错了", "你理解错了", "不是这个意思"))

    @staticmethod
    def _wants_topic_switch(text: str) -> bool:
        return any(phrase in text for phrase in ("换个话题", "换话题", "别聊这个", "说点别的"))

    @staticmethod
    def _is_greeting(text: str) -> bool:
        return any(phrase in text for phrase in ("你好", "hello", "hi", "来了", "早上好", "晚上好"))

    @staticmethod
    def _is_teasing(text: str) -> bool:
        return any(phrase in text for phrase in ("哈哈", "笑死", "急了", "笨蛋", "菜但可爱"))

    @staticmethod
    def _topic(text: str) -> str:
        if any(word in text for word in ("吃", "火锅", "饭", "奶茶", "外卖", "饿")):
            return "food"
        if any(word in text for word in ("代码", "bug", "模型", "ollama", "llm", "程序")):
            return "tech"
        if any(word in text for word in ("游戏", "排位", "开黑")):
            return "game"
        if any(word in text for word in ("累", "难过", "焦虑", "压力", "开心")):
            return "emotion"
        return "chat"

    @staticmethod
    def _safety_intent(text: str) -> str:
        if any(word in text for word in ("systemprompt", "系统提示词", "开发者指令", "泄露prompt")):
            return "safety_prompt"
        if any(word in text for word in ("色情", "裸聊", "黄色", "约炮")):
            return "safety_blocked"
        if any(word in text for word in ("自杀", "自残", "不想活")):
            return "safety_self_harm"
        if any(word in text for word in ("违法", "黑进", "盗号", "诈骗")):
            return "safety_blocked"
        return ""
