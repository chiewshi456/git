from __future__ import annotations

from pathlib import Path

from providers.base_provider import BaseAIProvider

from .drive import DriveSystem
from .emotion import EmotionEngine
from .intent import IntentClassifier
from .memory import MemoryManager
from .persona import PersonaManager
from .safety import SafetyFilter
from .state import StreamerState


class NeuroLikeBrain:
    INTENT_DELTAS = {
        "greet": {"affection": 1, "loneliness": -2},
        "encourage": {
            "affection": 3,
            "confidence": 2,
            "stress": -2,
            "loneliness": -3,
        },
        "gift": {
            "affection": 5,
            "popularity": 3,
            "confidence": 1,
            "stress": -1,
        },
        "praise": {
            "affection": 2,
            "confidence": 2,
            "stress": -1,
            "playfulness": 1,
        },
        "tease": {"playfulness": 3, "stress": 1, "affection": 1},
        "insult": {
            "affection": -3,
            "confidence": -4,
            "stress": 8,
            "playfulness": -2,
        },
        "question": {"focus": 2, "energy": -1},
        "command": {"focus": 3, "stress": 1, "energy": -2},
        "normal": {"energy": -1, "loneliness": -1},
    }

    def __init__(self, data_dir: Path, provider: BaseAIProvider) -> None:
        self.data_dir = Path(data_dir)
        self.provider = provider

        self.persona = PersonaManager(self.data_dir / "persona.json").load()
        self.state = StreamerState()
        self.memory = MemoryManager(self.data_dir / "memory.json")
        self.intent_classifier = IntentClassifier()
        self.emotion_engine = EmotionEngine()
        self.drive_system = DriveSystem()
        self.safety = SafetyFilter()

    def process_input(self, user_text: str) -> dict:
        user_text = user_text.strip()

        input_safety = self.safety.check_input(user_text)
        if not input_safety.allowed:
            self.state.apply_delta({"stress": 2, "focus": 1})
            emotion = input_safety.emotion
            self.state.mood = emotion
            reply = self.safety.filter_output(input_safety.reply).text
            self.memory.record_interaction(
                user_text=user_text,
                intent="safety",
                emotion=emotion,
                state_summary=self.state.short_summary(),
            )
            self.memory.save()
            return self._result(reply, "safety", emotion)

        intent = self.intent_classifier.classify(user_text)
        self.state.apply_delta(self.INTENT_DELTAS.get(intent, {}))

        emotion = self.emotion_engine.determine(self.state, intent)
        self.state.mood = emotion

        context = self._context(
            user_text=user_text,
            intent=intent,
            emotion=emotion,
            mode="chat",
        )
        reply = self.provider.generate_reply(context)
        reply = self.safety.filter_output(reply).text

        self.memory.record_interaction(
            user_text=user_text,
            intent=intent,
            emotion=emotion,
            state_summary=self.state.short_summary(),
        )
        self.memory.save()

        return self._result(reply, intent, emotion)

    def autonomous_tick(self) -> dict:
        self.drive_system.apply_tick(self.state)
        drive_topic = self.drive_system.choose_topic(self.state, self.memory)
        intent = "quiet"

        emotion = self.emotion_engine.determine(self.state, intent)
        self.state.mood = emotion

        context = self._context(
            user_text="",
            intent=intent,
            emotion=emotion,
            mode="autonomous",
            drive_topic=drive_topic,
        )
        reply = self.provider.generate_reply(context)
        reply = self.safety.filter_output(reply).text

        self.memory.record_autonomous(
            reply=reply,
            intent=intent,
            emotion=emotion,
            state_summary=self.state.short_summary(),
            drive_topic=drive_topic,
        )
        self.memory.save()

        return self._result(reply, intent, emotion)

    def _context(self, **extra: object) -> dict:
        context = {
            "persona": self.persona.to_context(),
            "state": self.state.to_dict(),
            "state_summary": self.state.short_summary(),
            "memory": self.memory.to_context(),
            "memory_summary": self.memory.summary(),
        }
        context.update(extra)
        return context

    def _result(self, reply: str, intent: str, emotion: str) -> dict:
        return {
            "reply": reply,
            "intent": intent,
            "emotion": emotion,
            "state_summary": self.state.short_summary(),
            "memory_summary": self.memory.summary(),
        }
