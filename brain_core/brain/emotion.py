from __future__ import annotations

from .state import StreamerState


class EmotionEngine:
    def detect(self, intent: str, state: StreamerState) -> str:
        if state.stress > 80:
            return "nervous"
        if state.energy < 15:
            return "tired"
        if state.confidence > 75 and state.playfulness > 50:
            return "smug"
        if state.loneliness > 80:
            return "lonely"

        if intent == "insult":
            return "annoyed" if state.self_control < 40 else "hurt"
        if intent == "gift":
            return "happy" if state.affection > 30 else "shy"
        if intent == "encourage":
            return "touched" if state.stress > 40 or state.confidence < 30 else "happy"
        if intent == "praise":
            return "shy" if state.confidence < 40 else "smug"
        if intent == "tease":
            return "playful" if state.playfulness > 50 else "nervous"
        if intent == "question":
            return "curious"
        if intent == "command":
            return "focused"
        if intent == "emotional_support":
            return "caring"
        if intent == "personal_question":
            return "shy" if state.trust < 25 else "curious"
        if intent == "silence":
            if state.loneliness > 50:
                return "lonely"
            if state.energy < 25:
                return "tired"
            return "nervous"
        if intent == "greet":
            return "happy"

        return "neutral"
