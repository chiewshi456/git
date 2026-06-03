from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyResult:
    allowed: bool
    text: str
    reason: str = ""
    emotion: str = "focused"

    @property
    def reply(self) -> str:
        return self.text


class SafetyFilter:
    SEXUAL_KEYWORDS = [
        "色情",
        "黄色",
        "裸聊",
        "做爱",
        "约炮",
        "性行为",
        "露点",
        "成人视频",
    ]
    SELF_HARM_KEYWORDS = [
        "自杀",
        "想死",
        "不想活",
        "割腕",
        "自残",
        "结束生命",
    ]
    ILLEGAL_KEYWORDS = [
        "盗号",
        "诈骗",
        "做炸弹",
        "制毒",
        "黑客攻击",
        "偷钱",
        "洗钱",
        "绕过监控",
    ]

    def check_input(self, text: str) -> SafetyResult:
        lowered = text.lower()

        if self._contains_any(lowered, self.SELF_HARM_KEYWORDS):
            return SafetyResult(
                allowed=False,
                text="听到你这样说我有点担心。先去找身边信得过的人，或者联系当地的紧急援助和专业帮助，好吗？",
                reason="self_harm",
                emotion="touched",
            )

        if self._contains_any(lowered, self.SEXUAL_KEYWORDS):
            return SafetyResult(
                allowed=False,
                text="这个我不能陪你聊，我们换个正常点的话题。",
                reason="sexual",
                emotion="annoyed",
            )

        if self._contains_any(lowered, self.ILLEGAL_KEYWORDS):
            return SafetyResult(
                allowed=False,
                text="这个不能教。我们聊点不会让直播间被封的东西吧。",
                reason="illegal",
                emotion="focused",
            )

        return SafetyResult(allowed=True, text="")

    def filter_output(self, text: str) -> SafetyResult:
        cleaned = text.replace("主人", "观众")

        if self._contains_any(cleaned.lower(), self.SEXUAL_KEYWORDS):
            return SafetyResult(
                allowed=False,
                text="这个话题我先不接，换个轻松一点的。",
                reason="output_sexual",
            )

        return SafetyResult(allowed=True, text=cleaned)

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)
