from __future__ import annotations

from dataclasses import dataclass

from .utils import clamp


INT_FIELDS = (
    "affection",
    "trust",
    "stress",
    "energy",
    "confidence",
    "loneliness",
    "playfulness",
    "curiosity",
    "focus",
    "self_control",
)


@dataclass
class StreamerState:
    mood: str = "nervous"
    affection: int = 0
    trust: int = 10
    stress: int = 25
    energy: int = 80
    confidence: int = 15
    loneliness: int = 20
    playfulness: int = 35
    curiosity: int = 50
    focus: int = 50
    self_control: int = 70

    def __post_init__(self) -> None:
        self.clamp()

    def clamp(self) -> None:
        for field_name in INT_FIELDS:
            setattr(self, field_name, clamp(getattr(self, field_name)))

    def apply_delta(self, deltas: dict[str, int]) -> None:
        for field_name, delta in deltas.items():
            if field_name in INT_FIELDS:
                setattr(self, field_name, getattr(self, field_name) + delta)
        self.clamp()

    def to_dict(self) -> dict:
        data = {"mood": self.mood}
        for field_name in INT_FIELDS:
            data[field_name] = getattr(self, field_name)
        return data

    def short_summary(self) -> str:
        return (
            f"mood={self.mood}, affection={self.affection}, trust={self.trust}, "
            f"stress={self.stress}, energy={self.energy}, confidence={self.confidence}, "
            f"loneliness={self.loneliness}"
        )

    def debug_summary(self) -> str:
        return (
            f"mood={self.mood}, affection={self.affection}, trust={self.trust}, "
            f"stress={self.stress}, energy={self.energy}, confidence={self.confidence}, "
            f"loneliness={self.loneliness}, playfulness={self.playfulness}, "
            f"curiosity={self.curiosity}, focus={self.focus}, "
            f"self_control={self.self_control}"
        )
