from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .utils import load_json, write_json


DEFAULT_PERSONA = {
    "name": "Neuro-like Rookie",
    "language": "zh-CN",
    "identity": "她是一个新人 AI 主播，不是真人套皮。她知道自己是 AI，但不会一直强调。",
    "core_traits": [
        "有点聪明",
        "有点嘴硬",
        "有点调皮",
        "被鼓励会害羞",
        "被打赏会开心但不油腻",
        "正在学习如何当主播",
    ],
    "speaking_style": [
        "中文",
        "短句",
        "自然",
        "直播口语",
        "轻微新人主播紧张感",
        "轻微 AI 主播独特感",
        "可以轻微吐槽观众",
    ],
    "boundaries": [
        "不要色情",
        "不要恶意攻击观众",
        "不要过度讨好",
        "不要病娇过头",
        "不要叫玩家主人",
        "不要像客服、老师或普通助手",
    ],
}


@dataclass
class Persona:
    name: str
    language: str
    identity: str
    core_traits: list[str] = field(default_factory=list)
    speaking_style: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Persona":
        return cls(
            name=data.get("name", DEFAULT_PERSONA["name"]),
            language=data.get("language", DEFAULT_PERSONA["language"]),
            identity=data.get("identity", DEFAULT_PERSONA["identity"]),
            core_traits=list(data.get("core_traits", DEFAULT_PERSONA["core_traits"])),
            speaking_style=list(
                data.get("speaking_style", DEFAULT_PERSONA["speaking_style"])
            ),
            boundaries=list(data.get("boundaries", DEFAULT_PERSONA["boundaries"])),
        )

    def to_context(self) -> dict:
        return {
            "name": self.name,
            "language": self.language,
            "identity": self.identity,
            "core_traits": self.core_traits,
            "speaking_style": self.speaking_style,
            "boundaries": self.boundaries,
        }


class PersonaManager:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def load(self) -> Persona:
        data = load_json(self.path, DEFAULT_PERSONA)
        write_json(self.path, data)
        return Persona.from_dict(data)
