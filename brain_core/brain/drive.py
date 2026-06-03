from __future__ import annotations

from dataclasses import dataclass

from .state import StreamerState


@dataclass
class DriveScore:
    name: str
    score: float

    def to_dict(self) -> dict:
        return {"name": self.name, "score": round(self.score, 2)}


class DriveSystem:
    def compute(self, state: StreamerState) -> list[dict]:
        scores = [
            DriveScore(
                "wants_attention",
                state.loneliness * 0.7 + state.stress * 0.2,
            ),
            DriveScore(
                "wants_to_talk",
                state.curiosity * 0.6 + state.playfulness * 0.3,
            ),
            DriveScore(
                "wants_to_tease",
                state.playfulness * 0.8 - state.stress * 0.2,
            ),
            DriveScore(
                "wants_to_impress",
                state.confidence * 0.5 + state.affection * 0.3,
            ),
            DriveScore("wants_to_rest", 100 - state.energy),
            DriveScore(
                "wants_to_avoid_conflict",
                state.stress * 0.5 + (100 - state.self_control) * 0.5,
            ),
            DriveScore(
                "wants_to_learn_about_viewer",
                state.curiosity * 0.6 + state.trust * 0.2,
            ),
        ]
        scores.sort(key=lambda item: item.score, reverse=True)
        return [item.to_dict() for item in scores[:2]]
