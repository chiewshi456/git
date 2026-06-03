from __future__ import annotations

from .state import StreamerState


class GrowthSystem:
    LEVEL_STEP = 25

    def apply(
        self,
        memory_data: dict,
        state: StreamerState,
        learning_result: dict,
        intent: str,
    ) -> dict:
        growth = memory_data.setdefault("growth", self.default_growth())
        previous_level = growth.get("level", 1)

        xp_gain = self._xp_gain(learning_result, intent)
        growth["xp"] = int(growth.get("xp", 0)) + xp_gain
        growth["level"] = max(1, growth["xp"] // self.LEVEL_STEP + 1)
        growth["stage"] = self._stage_for_level(growth["level"])
        growth["unlocked_traits"] = self._traits_for_level(growth["level"])
        growth["total_learning_events"] = int(growth.get("total_learning_events", 0))

        if learning_result.get("learning_note"):
            growth["total_learning_events"] += 1

        level_up = growth["level"] > previous_level
        if level_up:
            state.apply_delta({"confidence": 1, "curiosity": 1, "stress": -1})

        return {
            "xp_gain": xp_gain,
            "level": growth["level"],
            "stage": growth["stage"],
            "level_up": level_up,
            "unlocked_traits": growth["unlocked_traits"],
        }

    @staticmethod
    def default_growth() -> dict:
        return {
            "level": 1,
            "xp": 0,
            "stage": "booting",
            "unlocked_traits": ["basic_memory"],
            "total_learning_events": 0,
        }

    def _xp_gain(self, learning_result: dict, intent: str) -> int:
        xp = 1
        if intent in {"question", "personal_question", "emotional_support", "command"}:
            xp += 1
        if learning_result.get("topics"):
            xp += 1
        if learning_result.get("learned_preferences"):
            xp += 2
        if learning_result.get("feedback") in {"positive", "negative"}:
            xp += 1
        if learning_result.get("style_signal") != "none":
            xp += 1
        return xp

    @staticmethod
    def _stage_for_level(level: int) -> str:
        if level < 3:
            return "booting"
        if level < 5:
            return "learning"
        if level < 8:
            return "adaptive"
        return "stable"

    @staticmethod
    def _traits_for_level(level: int) -> list[str]:
        traits = ["basic_memory"]
        if level >= 2:
            traits.append("topic_awareness")
        if level >= 3:
            traits.append("feedback_adaptation")
        if level >= 4:
            traits.append("style_tuning")
        if level >= 5:
            traits.append("self_reflection")
        return traits
