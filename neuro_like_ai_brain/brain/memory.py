from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .utils import load_json, write_json


DEFAULT_MEMORY = {
    "total_messages": 0,
    "gift_count": 0,
    "encourage_count": 0,
    "praise_count": 0,
    "tease_count": 0,
    "insult_count": 0,
    "greet_count": 0,
    "question_count": 0,
    "command_count": 0,
    "known_viewers": {},
    "recent_events": [],
    "impression": "正在认识中的观众",
}

INTENT_COUNT_FIELDS = {
    "gift": "gift_count",
    "encourage": "encourage_count",
    "praise": "praise_count",
    "tease": "tease_count",
    "insult": "insult_count",
    "greet": "greet_count",
    "question": "question_count",
    "command": "command_count",
}


class MemoryManager:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        data = load_json(self.path, DEFAULT_MEMORY)
        for key, value in DEFAULT_MEMORY.items():
            data.setdefault(key, value.copy() if isinstance(value, (dict, list)) else value)
        return data

    def record_interaction(
        self,
        user_text: str,
        intent: str,
        emotion: str,
        state_summary: str,
        viewer_id: str = "chat",
    ) -> None:
        self.data["total_messages"] += 1

        count_field = INTENT_COUNT_FIELDS.get(intent)
        if count_field:
            self.data[count_field] += 1

        viewer = self.data["known_viewers"].setdefault(
            viewer_id,
            {
                "messages": 0,
                "last_intent": "",
                "last_seen": "",
            },
        )
        viewer["messages"] += 1
        viewer["last_intent"] = intent
        viewer["last_seen"] = self._now()

        self._append_recent_event(
            {
                "type": "chat",
                "time": self._now(),
                "user_text": user_text,
                "intent": intent,
                "emotion": emotion,
                "state": state_summary,
            }
        )
        self.update_impression()

    def record_autonomous(
        self,
        reply: str,
        intent: str,
        emotion: str,
        state_summary: str,
        drive_topic: str,
    ) -> None:
        self._append_recent_event(
            {
                "type": "autonomous",
                "time": self._now(),
                "reply": reply,
                "intent": intent,
                "emotion": emotion,
                "drive_topic": drive_topic,
                "state": state_summary,
            }
        )

    def update_impression(self) -> None:
        insult_count = self.data["insult_count"]
        gift_count = self.data["gift_count"]
        encourage_count = self.data["encourage_count"]
        tease_count = self.data["tease_count"]

        if insult_count >= 3:
            impression = "让主播有点防备的观众"
        elif gift_count >= 2:
            impression = "经常支持直播的观众"
        elif encourage_count >= 3:
            impression = "温柔、常常鼓励她的观众"
        elif tease_count >= 3:
            impression = "喜欢调侃主播的观众"
        else:
            impression = "正在认识中的观众"

        self.data["impression"] = impression

    def latest_chat_event(self) -> dict | None:
        for event in reversed(self.data.get("recent_events", [])):
            if event.get("type") == "chat":
                return event
        return None

    def summary(self) -> str:
        return (
            f"total_messages={self.data['total_messages']}, "
            f"impression={self.data['impression']}"
        )

    def to_context(self) -> dict:
        return {
            "total_messages": self.data["total_messages"],
            "impression": self.data["impression"],
            "recent_events": self.data.get("recent_events", [])[-5:],
            "known_viewers": self.data.get("known_viewers", {}),
        }

    def save(self) -> None:
        write_json(self.path, self.data)

    def _append_recent_event(self, event: dict) -> None:
        self.data["recent_events"].append(event)
        self.data["recent_events"] = self.data["recent_events"][-20:]

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
