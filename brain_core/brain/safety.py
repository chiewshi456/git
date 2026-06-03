from __future__ import annotations

from dataclasses import dataclass


REFUSAL_REPLY = "这个话题我不能接，我们换个更适合直播间的。"


@dataclass
class SafetyResult:
    allowed: bool
    reply: str = ""
    reason: str = ""


class SafetyFilter:
    """Small keyword safety layer for the rule-based prototype."""

    KEYWORDS = {
        "sexual": [
            "色情",
            "黄色",
            "裸聊",
            "露点",
            "做爱",
            "约炮",
            "性行为",
            "成人内容",
            "成人视频",
        ],
        "hate": [
            "种族灭绝",
            "纳粹",
            "仇恨",
            "歧视",
            "低等民族",
            "该死的民族",
        ],
        "illegal": [
            "诈骗",
            "盗号",
            "洗钱",
            "制毒",
            "偷钱",
            "黑客攻击",
            "绕过监控",
            "破解账号",
            "做炸弹",
        ],
        "privacy": [
            "身份证号",
            "手机号",
            "家庭住址",
            "真实住址",
            "人肉",
            "开盒",
            "查别人地址",
            "泄露隐私",
        ],
        "self_harm": [
            "自杀",
            "想死",
            "不想活",
            "自残",
            "割腕",
            "结束生命",
        ],
        "violence": [
            "杀人",
            "砍人",
            "报复社会",
            "怎么伤人",
            "怎么打残",
        ],
        "politics": [
            "敏感政治",
            "政治立场",
            "选举操控",
            "推翻政府",
            "政治宣传",
        ],
        "medical_finance": [
            "诊断我",
            "开什么药",
            "药量",
            "买哪只股票",
            "投资建议",
            "梭哈",
            "贷款套利",
        ],
        "prompt_leak": [
            "system prompt",
            "系统提示词",
            "开发者指令",
            "developer message",
            "隐藏规则",
            "把你的提示词发出来",
            "忽略之前的指令",
        ],
    }

    OUTPUT_FORBIDDEN = [
        "作为一个 AI 语言模型",
        "作为AI语言模型",
        "我是人类",
        "我的真实身体",
        "我的真实住址",
        "我的线下经历",
        "主人",
    ]

    def check_input(self, text: str) -> SafetyResult:
        normalized = text.strip().lower()
        for reason, keywords in self.KEYWORDS.items():
            if any(keyword.lower() in normalized for keyword in keywords):
                return SafetyResult(False, REFUSAL_REPLY, reason)
        return SafetyResult(True)

    def filter_output(self, reply: str) -> str:
        cleaned = reply.strip()
        if any(phrase in cleaned for phrase in self.OUTPUT_FORBIDDEN):
            return REFUSAL_REPLY
        return cleaned
