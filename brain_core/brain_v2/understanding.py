from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from brain.ollama_client import OllamaClient


@dataclass
class Understanding:
    user_act: str = "chat"
    topic: str = ""
    user_goal: str = ""
    emotional_tone: str = "neutral"
    refers_to_previous: bool = False
    wants_topic_switch: bool = False
    continue_old_topic: bool = False
    should_apologize: bool = False
    complaint_target: str = ""
    stable_memory_candidates: list[dict] = field(default_factory=list)
    confidence: float = 0.5
    raw: str = ""
    source: str = "fallback"

    def to_dict(self) -> dict:
        return {
            "user_act": self.user_act,
            "topic": self.topic,
            "user_goal": self.user_goal,
            "emotional_tone": self.emotional_tone,
            "refers_to_previous": self.refers_to_previous,
            "wants_topic_switch": self.wants_topic_switch,
            "continue_old_topic": self.continue_old_topic,
            "should_apologize": self.should_apologize,
            "complaint_target": self.complaint_target,
            "stable_memory_candidates": self.stable_memory_candidates,
            "confidence": self.confidence,
            "raw": self.raw,
            "source": self.source,
        }


class UnderstandingEngine:
    """LLM-first structured interpretation with deterministic fallback."""

    USER_ACTS = {
        "chat",
        "question",
        "correction",
        "feedback",
        "topic_switch",
        "memory_query",
        "identity_query",
        "self_status_query",
        "preference_share",
        "name_share",
        "teasing",
        "greeting",
        "silence",
    }

    TOPIC_KEYWORDS = {
        "food": ("吃", "火锅", "外卖", "奶茶", "饿", "饭", "宵夜"),
        "brain": ("上下文", "逻辑", "智能", "记忆", "对话", "理解", "脑"),
        "tech": ("代码", "bug", "报错", "模型", "ollama", "llm", "程序"),
        "game": ("游戏", "排位", "开黑", "通关"),
        "work": ("工作", "上班", "加班", "老板", "同事", "累"),
        "emotion": ("难过", "开心", "焦虑", "压力", "不舒服"),
    }

    def __init__(self, ollama: OllamaClient | None = None, enabled: bool = True) -> None:
        self.ollama = ollama
        self.enabled = enabled and ollama is not None

    def analyze(self, user_input: str, memory: dict) -> Understanding:
        text = user_input.strip()
        fallback = self._fallback(text, memory)
        if not self.enabled or not text:
            return fallback
        if self._should_use_fast_understanding(fallback):
            return fallback

        prompt = self._build_prompt(text, memory)
        raw = self.ollama.generate_raw(
            prompt,
            options={"temperature": 0.1, "top_p": 0.8, "num_predict": 260},
            response_format="json",
        )
        parsed = self._parse_json(raw)
        if not parsed:
            fallback.raw = raw
            return fallback

        result = self._from_json(parsed, fallback)
        if result.confidence < 0.45:
            fallback.raw = raw
            fallback.source = "fallback_low_confidence"
            return fallback
        result = self._apply_hard_overrides(result, fallback)
        result = self._fix_spurious_topic_switch(result, fallback)
        result.raw = raw
        result.source = "llm_json"
        return result

    def _build_prompt(self, user_input: str, memory: dict) -> str:
        conversation = memory.get("conversation_context", {})
        profile = memory.get("viewer_profile", {})
        return "\n".join(
            [
                "你是对话理解模块，不负责回复用户。",
                "任务：把用户当前输入解析成严格 JSON，帮助 AI 大脑判断上下文和逻辑。",
                "不要聊天，不要扮演 Mika，只输出 JSON。",
                "",
                "字段：",
                "user_act: chat/question/correction/feedback/topic_switch/memory_query/identity_query/self_status_query/preference_share/name_share/teasing/greeting/silence",
                "topic: food/brain/tech/game/work/emotion/identity/memory/none",
                "user_goal: 一句话说明用户真实目的",
                "emotional_tone: neutral/playful/annoyed/frustrated/kind/sad",
                "refers_to_previous: true/false",
                "wants_topic_switch: true/false",
                "continue_old_topic: true/false",
                "should_apologize: true/false",
                "complaint_target: context/logic/memory/persona/reply_style/none",
                "stable_memory_candidates: [{type,key,value}]，只放用户明确说出的长期信息",
                "confidence: 0到1",
                "",
                "重要规则：",
                "用户说“不是”“你理解错了”“上下文差”“逻辑差”时，通常是 correction/feedback，不是继续旧话题。",
                "用户说“换个话题”时 wants_topic_switch=true，continue_old_topic=false。",
                "用户问“你现在在干嘛”“你吃了吗”时不要继承旧话题。",
                "",
                f"上一轮用户：{conversation.get('last_user_input', '')}",
                f"上一轮 Mika：{conversation.get('last_ai_reply', '')}",
                f"当前话题：{conversation.get('current_topic', '')}",
                f"已知用户名字：{profile.get('name', '')}",
                f"当前用户输入：{user_input}",
                "",
                "输出 JSON：",
            ]
        )

    def _fallback(self, text: str, memory: dict) -> Understanding:
        if not text:
            return Understanding(user_act="silence", topic="", source="fallback")

        topic = self._detect_topic(text)
        lowered = text.lower()
        user_act = "chat"
        complaint_target = ""
        should_apologize = False
        wants_topic_switch = any(word in text for word in ("换个话题", "换话题", "别聊这个", "说点别的"))
        refers = any(word in text for word in ("刚才", "刚刚", "上一句", "你说的", "不是", "为什么这么"))

        if any(word in text for word in ("上下文", "逻辑", "不够智能", "没有记忆力", "记忆力差", "答非所问")):
            user_act = "feedback"
            topic = "brain"
            should_apologize = True
            if "上下文" in text or "答非所问" in text:
                complaint_target = "context"
            elif "逻辑" in text or "不够智能" in text:
                complaint_target = "logic"
            elif "记忆" in text:
                complaint_target = "memory"
        elif wants_topic_switch:
            user_act = "topic_switch"
        elif any(word in text for word in ("你好", "hello", "hi", "来了")):
            user_act = "greeting"
        elif self._extract_name(text):
            user_act = "name_share"
        elif self._extract_preference(text):
            user_act = "preference_share"
        elif self._is_viewer_memory_query(text):
            user_act = "memory_query"
            topic = "memory"
        elif any(word in lowered for word in ("你是不是ai", "你是ai", "你是真人")):
            user_act = "identity_query"
            topic = "identity"
        elif any(word in text for word in ("你现在在干嘛", "你在干嘛", "你干嘛", "你吃了吗", "你吃饭了吗")):
            user_act = "self_status_query"
        elif any(word in text for word in ("只会这一句", "一直重复", "又是这句", "老是这句")):
            user_act = "feedback"
            topic = "brain"
            should_apologize = True
            complaint_target = "reply_style"
        elif "？" in text or "?" in text or any(word in text for word in ("为什么", "怎么", "什么", "吗")):
            user_act = "question"
        elif "哈哈" in text or "笑死" in text:
            user_act = "teasing"

        candidates = []
        name = self._extract_name(text)
        if name:
            candidates.append({"type": "viewer_name", "key": "name", "value": name})
        preference = self._extract_preference(text)
        if preference:
            candidates.append({"type": "viewer_preference", "key": "likes", "value": preference})

        return Understanding(
            user_act=user_act,
            topic=topic,
            user_goal=self._goal_for(user_act, complaint_target),
            emotional_tone="frustrated" if should_apologize else "neutral",
            refers_to_previous=refers,
            wants_topic_switch=wants_topic_switch,
            continue_old_topic=refers and not wants_topic_switch and user_act != "feedback",
            should_apologize=should_apologize,
            complaint_target=complaint_target or "none",
            stable_memory_candidates=candidates,
            confidence=0.65,
            source="fallback",
        )

    def _from_json(self, data: dict, fallback: Understanding) -> Understanding:
        user_act = str(data.get("user_act", fallback.user_act))
        if user_act not in self.USER_ACTS:
            user_act = fallback.user_act

        topic = str(data.get("topic", fallback.topic)).strip()
        if topic == "none":
            topic = ""

        candidates = data.get("stable_memory_candidates", [])
        if not isinstance(candidates, list):
            candidates = []

        return Understanding(
            user_act=user_act,
            topic=topic or fallback.topic,
            user_goal=str(data.get("user_goal", fallback.user_goal))[:160],
            emotional_tone=str(data.get("emotional_tone", fallback.emotional_tone)),
            refers_to_previous=bool(data.get("refers_to_previous", fallback.refers_to_previous)),
            wants_topic_switch=bool(data.get("wants_topic_switch", fallback.wants_topic_switch)),
            continue_old_topic=bool(data.get("continue_old_topic", fallback.continue_old_topic)),
            should_apologize=bool(data.get("should_apologize", fallback.should_apologize)),
            complaint_target=str(data.get("complaint_target", fallback.complaint_target)),
            stable_memory_candidates=candidates[:5],
            confidence=self._confidence(data.get("confidence", fallback.confidence)),
        )

    def _apply_hard_overrides(self, result: Understanding, fallback: Understanding) -> Understanding:
        critical_acts = {
            "feedback",
            "correction",
            "topic_switch",
            "self_status_query",
            "identity_query",
            "memory_query",
            "name_share",
            "preference_share",
        }
        if fallback.user_act not in critical_acts:
            return result

        # These cases are explicit surface forms. Do not let the model carry old
        # context into them.
        result.user_act = fallback.user_act
        result.topic = fallback.topic
        result.user_goal = fallback.user_goal
        result.refers_to_previous = fallback.refers_to_previous
        result.wants_topic_switch = fallback.wants_topic_switch
        result.continue_old_topic = fallback.continue_old_topic
        result.should_apologize = fallback.should_apologize
        result.complaint_target = fallback.complaint_target
        if fallback.stable_memory_candidates:
            result.stable_memory_candidates = fallback.stable_memory_candidates
        result.confidence = max(result.confidence, fallback.confidence)
        return result

    def _fix_spurious_topic_switch(self, result: Understanding, fallback: Understanding) -> Understanding:
        if fallback.wants_topic_switch:
            return result
        if result.user_act != "topic_switch" and not result.wants_topic_switch:
            return result

        result.user_act = fallback.user_act
        result.wants_topic_switch = False
        result.continue_old_topic = fallback.continue_old_topic
        result.should_apologize = fallback.should_apologize
        result.complaint_target = fallback.complaint_target
        result.user_goal = fallback.user_goal
        if fallback.topic:
            result.topic = fallback.topic
        if fallback.stable_memory_candidates:
            result.stable_memory_candidates = fallback.stable_memory_candidates
        return result

    @staticmethod
    def _should_use_fast_understanding(fallback: Understanding) -> bool:
        if fallback.user_act == "question" and fallback.topic:
            return True
        if fallback.user_act == "chat" and fallback.topic:
            return True
        return fallback.user_act in {
            "feedback",
            "correction",
            "topic_switch",
            "memory_query",
            "identity_query",
            "self_status_query",
            "preference_share",
            "name_share",
            "greeting",
            "teasing",
            "silence",
        }

    def _detect_topic(self, text: str) -> str:
        lowered = text.lower()
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                target = lowered if keyword.isascii() else text
                if keyword.lower() in target:
                    return topic
        return ""

    def _extract_name(self, text: str) -> str:
        match = re.search(
            r"(?:我叫|你可以叫我)(?!什么|啥|谁|名字)([\u4e00-\u9fffA-Za-z0-9_-]{1,16})",
            text,
        )
        return match.group(1).strip() if match else ""

    def _extract_preference(self, text: str) -> str:
        match = re.search(r"我喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)", text)
        return match.group(1).strip()[:40] if match else ""

    @staticmethod
    def _is_viewer_memory_query(text: str) -> bool:
        phrases = (
            "记得我",
            "还记得我",
            "认识我吗",
            "知道我是谁",
            "你知道我是谁",
            "我是谁",
            "我叫什么",
            "我叫啥",
            "我的名字",
            "我喜欢什么",
            "我不喜欢什么",
        )
        if any(phrase in text for phrase in phrases):
            return True
        return bool(re.search(r"你.*知道.*我.*(谁|名字|叫什么)", text))

    @staticmethod
    def _goal_for(user_act: str, complaint_target: str) -> str:
        if user_act == "feedback":
            return f"指出 AI 的{complaint_target or '回复'}问题，希望它修正"
        if user_act == "topic_switch":
            return "停止当前话题，换一个新话题"
        if user_act == "self_status_query":
            return "询问 AI 当前状态或身份相关生活问题"
        return "普通对话"

    @staticmethod
    def _parse_json(raw: str) -> dict:
        if not raw:
            return {}
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

    @staticmethod
    def _confidence(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, number))
