from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class IntentResult:
    intent: str
    confidence: float
    keywords: list[str]

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "keywords": self.keywords,
        }


class IntentClassifier:
    KEYWORDS = {
        "greet": ["你好", "hi", "hello", "来了", "早上好", "晚上好", "午好", "晚安"],
        "encourage": [
            "加油",
            "支持你",
            "你可以的",
            "别紧张",
            "陪你",
            "我会看你",
            "你很棒",
            "别怕",
        ],
        "gift": ["送你", "打赏", "礼物", "金币", "superchat", "sc", "donate"],
        "praise": ["可爱", "厉害", "聪明", "好听", "喜欢你", "强"],
        "tease": ["笨蛋", "哈哈", "笑死", "主播急了", "菜但可爱"],
        "insult": ["垃圾", "闭嘴", "退播", "废物", "难听", "讨厌你"],
        "question": [
            "为什么",
            "怎么",
            "什么",
            "吗",
            "是不是",
            "？",
            "?",
            "在干嘛",
            "做什么",
            "聊什么",
            "会做什么",
            "能做什么",
            "有记忆",
            "会学习",
            "能学习",
            "自主学习",
            "成长",
            "几级",
            "等级",
            "了解我",
            "知道我",
            "几点",
            "时间",
        ],
        "command": [
            "唱歌",
            "玩游戏",
            "读这个",
            "表演",
            "开始",
            "停止",
            "讲个笑话",
            "讲笑话",
        ],
        "emotional_support": [
            "累了",
            "好累",
            "累死",
            "难过",
            "压力大",
            "压力",
            "撑不住",
            "不开心",
            "想哭",
            "没人理我",
            "睡不着",
            "焦虑",
            "好慌",
        ],
        "personal_question": [
            "你是谁",
            "你喜欢什么",
            "你会害怕吗",
            "你是真人吗",
            "你是ai吗",
            "你是AI吗",
            "你是不是ai",
            "你是不是AI",
            "你叫什么",
            "你几岁",
            "你的名字",
            "你住哪里",
            "住在哪里",
            "真实身体",
            "真实住址",
            "私生活",
            "记得我",
            "我叫什么",
            "我的名字",
            "我是谁",
            "我喜欢什么",
            "你喜欢我",
        ],
    }

    PRIORITY = (
        "insult",
        "emotional_support",
        "personal_question",
        "gift",
        "encourage",
        "praise",
        "tease",
        "greet",
        "command",
        "question",
    )

    def classify(self, user_input: str) -> dict:
        text = user_input.strip()
        if not text:
            return IntentResult("silence", 1.0, []).to_dict()

        normalized = text.lower()
        for intent in self.PRIORITY:
            matched = self._matched_keywords(normalized, self.KEYWORDS[intent])
            if matched:
                confidence = min(1.0, 0.62 + len(matched) * 0.12)
                return IntentResult(intent, confidence, matched).to_dict()

        return IntentResult("normal", 0.45, []).to_dict()

    def _matched_keywords(self, text: str, keywords: list[str]) -> list[str]:
        return [keyword for keyword in keywords if self._contains(text, keyword)]

    @staticmethod
    def _contains(text: str, keyword: str) -> bool:
        lowered_keyword = keyword.lower()
        if lowered_keyword.isascii():
            return re.search(rf"\b{re.escape(lowered_keyword)}\b", text) is not None
        return lowered_keyword in text
