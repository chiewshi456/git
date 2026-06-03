from __future__ import annotations

from .state import StreamerState


class EmotionEngine:
    def determine(self, state: StreamerState, intent: str) -> str:
        if intent == "insult":
            return "hurt" if state.confidence < 35 else "annoyed"

        if intent == "gift":
            return "shy" if state.affection < 40 else "happy"

        if intent == "encourage" and state.confidence < 35:
            return "touched"

        if intent == "praise":
            return "shy" if state.confidence < 60 else "smug"

        if intent == "tease":
            return "playful" if state.playfulness >= 35 else "annoyed"

        if intent in {"question", "command"}:
            return "focused"

        if intent == "greet":
            return "happy" if state.loneliness < 40 else "touched"

        if state.stress > 70:
            return "nervous"

        if state.loneliness > 60:
            return "lonely"

        if state.confidence > 60:
            return "confident"

        if state.affection > 50 and state.stress < 40:
            return "happy"

        if intent == "quiet":
            if state.energy < 25:
                return "nervous"
            if state.playfulness > 55:
                return "playful"
            return "lonely" if state.loneliness > 35 else "nervous"

        return "happy" if state.affection > 15 else "nervous"
