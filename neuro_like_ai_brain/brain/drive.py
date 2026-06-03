from __future__ import annotations

import random

from .memory import MemoryManager
from .state import StreamerState


class DriveSystem:
    def __init__(self) -> None:
        self.random = random.Random()

    def apply_tick(self, state: StreamerState) -> None:
        state.apply_delta(
            {
                "loneliness": 2,
                "energy": -1,
                "stress": 1,
            }
        )

    def choose_topic(self, state: StreamerState, memory: MemoryManager) -> str:
        if state.energy < 25:
            return "low_energy"

        if state.loneliness > 60:
            return "lonely"

        if state.stress > 70:
            return "stress"

        latest = memory.latest_chat_event()
        if latest and latest.get("intent") in {"gift", "encourage", "praise", "tease"}:
            return "recent_memory"

        if state.playfulness > 55:
            return "tease_quiet"

        return self.random.choice(
            [
                "ask_question",
                "self_talk",
                "quiet",
                "find_topic",
            ]
        )
