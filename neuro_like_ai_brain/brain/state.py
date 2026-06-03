from __future__ import annotations

from dataclasses import dataclass

from .utils import clamp


NUMERIC_FIELDS = (
    "affection",
    "popularity",
    "stress",
    "energy",
    "confidence",
    "loneliness",
    "playfulness",
    "focus",
)


@dataclass
class StreamerState:
    mood: str = "nervous"
    affection: int = 0
    popularity: int = 0
    stress: int = 20
    energy: int = 80
    confidence: int = 10
    loneliness: int = 10
    playfulness: int = 30
    focus: int = 50

    def __post_init__(self) -> None:
        for field_name in NUMERIC_FIELDS:
            setattr(self, field_name, clamp(getattr(self, field_name)))

    @staticmethod
    def clamp(value: int) -> int:
        return clamp(value)

    def apply_delta(self, deltas: dict[str, int]) -> None:
        for field_name, delta in deltas.items():
            if field_name not in NUMERIC_FIELDS:
                continue
            current = getattr(self, field_name)
            setattr(self, field_name, clamp(current + delta))

    def to_dict(self) -> dict:
        data = {"mood": self.mood}
        for field_name in NUMERIC_FIELDS:
            data[field_name] = getattr(self, field_name)
        return data

    def short_summary(self) -> str:
        return (
            f"affection={self.affection}, "
            f"popularity={self.popularity}, "
            f"stress={self.stress}, "
            f"energy={self.energy}, "
            f"confidence={self.confidence}, "
            f"loneliness={self.loneliness}, "
            f"playfulness={self.playfulness}, "
            f"focus={self.focus}"
        )
