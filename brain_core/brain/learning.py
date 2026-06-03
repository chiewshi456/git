from __future__ import annotations

import re


class LearningSystem:
    TOPIC_KEYWORDS = {
        "food": ("吃饭", "外卖", "奶茶", "饿", "宵夜", "早餐", "午饭", "晚饭"),
        "sleep": ("睡觉", "困", "熬夜", "晚安", "睡不着"),
        "study": ("学习", "作业", "考试", "复习", "上课", "学校"),
        "work": ("工作", "上班", "老板", "同事", "加班", "下班"),
        "game": ("游戏", "开黑", "排位", "通关", "手柄", "鼠标"),
        "music": ("音乐", "唱歌", "歌单", "听歌", "旋律"),
        "weather": ("天气", "下雨", "好热", "好冷", "降温", "太阳"),
        "anime": ("动漫", "动画", "漫画", "番", "二次元", "角色"),
        "tech": ("编程", "代码", "AI", "人工智能", "模型", "程序", "bug"),
        "ai_self": ("学习", "成长", "记忆", "思考", "智能", "意识"),
    }

    POSITIVE_FEEDBACK = (
        "哈哈",
        "笑死",
        "不错",
        "可以",
        "喜欢这样",
        "这样好",
        "有意思",
        "聪明",
        "可爱",
        "好用",
        "对",
    )
    NEGATIVE_FEEDBACK = (
        "尬",
        "死板",
        "不像",
        "别这样",
        "不喜欢",
        "没逻辑",
        "答非所问",
        "太客服",
        "太长",
        "太短",
    )

    STYLE_SIGNALS = {
        "caring": ("温柔点", "安慰我", "陪我", "认真听"),
        "playful": ("调皮点", "嘴硬点", "吐槽我", "接梗"),
        "direct": ("直接说", "短一点", "别废话", "简单说"),
        "detailed": ("详细点", "多说点", "解释一下", "认真讲"),
    }

    def analyze(self, user_input: str, intent: str, reply_intent: str) -> dict:
        text = user_input.strip()
        topics = self._detect_topics(text)
        feedback = self._detect_feedback(text)
        style_signal = self._detect_style_signal(text)

        learned_preferences = []
        like = self._extract_like(text)
        dislike = self._extract_dislike(text)
        if like:
            learned_preferences.append({"type": "like", "value": like})
        if dislike:
            learned_preferences.append({"type": "dislike", "value": dislike})

        learning_note = self._make_learning_note(
            topics=topics,
            feedback=feedback,
            style_signal=style_signal,
            learned_preferences=learned_preferences,
        )

        return {
            "topics": topics,
            "feedback": feedback,
            "style_signal": style_signal,
            "learned_preferences": learned_preferences,
            "reply_intent": reply_intent,
            "intent": intent,
            "learning_note": learning_note,
        }

    def _detect_topics(self, text: str) -> list[str]:
        return [
            topic
            for topic, keywords in self.TOPIC_KEYWORDS.items()
            if any(keyword in text for keyword in keywords)
        ]

    def _detect_feedback(self, text: str) -> str:
        if any(keyword in text for keyword in self.NEGATIVE_FEEDBACK):
            return "negative"
        if any(keyword in text for keyword in self.POSITIVE_FEEDBACK):
            return "positive"
        return "neutral"

    def _detect_style_signal(self, text: str) -> str:
        for style, keywords in self.STYLE_SIGNALS.items():
            if any(keyword in text for keyword in keywords):
                return style
        return "none"

    def _extract_like(self, text: str) -> str | None:
        match = re.search(r"我喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)", text)
        if match:
            return match.group(1).strip()[:24]
        return None

    def _extract_dislike(self, text: str) -> str | None:
        match = re.search(r"我不喜欢(.+?)(?:[，。,.!！?？\s]|$)", text)
        if match:
            return match.group(1).strip()[:24]
        return None

    def _make_learning_note(
        self,
        topics: list[str],
        feedback: str,
        style_signal: str,
        learned_preferences: list[dict],
    ) -> str:
        if learned_preferences:
            item = learned_preferences[-1]
            action = "喜欢" if item["type"] == "like" else "不喜欢"
            return f"用户{action}{item['value']}"
        if feedback != "neutral":
            return f"用户给出了{feedback}反馈"
        if style_signal != "none":
            return f"用户偏好{style_signal}风格"
        if topics:
            return f"用户正在聊{topics[0]}"
        return ""
