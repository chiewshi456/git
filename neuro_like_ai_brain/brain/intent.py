from __future__ import annotations

import re


class IntentClassifier:
    KEYWORDS = {
        "greet": ["你好", "hello", "hi", "来了", "晚上好", "早上好"],
        "encourage": ["加油", "支持你", "别紧张", "我会看你", "陪你", "你可以的"],
        "gift": ["送你", "打赏", "金币", "礼物", "superchat", "sc", "donate"],
        "praise": ["可爱", "厉害", "好听", "喜欢你", "聪明", "强"],
        "tease": ["笨蛋", "菜但可爱", "哈哈", "笑死", "主播急了"],
        "insult": ["垃圾", "难听", "退播", "废物", "闭嘴", "讨厌你"],
        "command": ["唱歌", "玩游戏", "读这个", "表演", "开始", "停止"],
    }

    QUESTION_WORDS = ["为什么", "怎么", "什么", "吗", "是不是"]

    def classify(self, text: str) -> str:
        normalized = text.strip().lower()
        if not normalized:
            return "normal"

        # 明显负面输入优先，避免被“哈哈”等词盖过去。
        if self._contains_any(normalized, self.KEYWORDS["insult"]):
            return "insult"

        for intent in (
            "gift",
            "encourage",
            "praise",
            "tease",
            "greet",
            "command",
        ):
            if self._contains_any(normalized, self.KEYWORDS[intent]):
                return intent

        if "?" in normalized or "？" in normalized:
            return "question"

        if self._contains_any(normalized, self.QUESTION_WORDS):
            return "question"

        return "normal"

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(self._contains_keyword(text, keyword) for keyword in keywords)

    @staticmethod
    def _contains_keyword(text: str, keyword: str) -> bool:
        if keyword.isascii():
            return re.search(rf"\b{re.escape(keyword.lower())}\b", text) is not None
        return keyword in text
