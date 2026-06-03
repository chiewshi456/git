from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_MEMORY: dict[str, Any] = {
    "schema_version": "mika_brain_v3",
    "viewer": {
        "name": "",
        "aliases": [],
        "likes": [],
        "dislikes": [],
        "facts": [],
    },
    "self": {
        "improvement_notes": [],
        "style_notes": [
            "短句",
            "中文口语",
            "机灵但不要攻击用户",
            "承认自己是 AI，不假装真人",
        ],
    },
    "conversation": {
        "turns": [],
        "current_topic": "",
    },
    "stats": {
        "total_turns": 0,
        "fast_turns": 0,
        "llm_turns": 0,
    },
}


class MemoryStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.path = self.data_dir / "mika_v3_memory.json"
        self.legacy_path = self.data_dir / "memory.json"
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            return self._normalize(self._read_json(self.path))

        data = deepcopy(DEFAULT_MEMORY)
        if self.legacy_path.exists():
            self._import_legacy(data, self._read_json(self.legacy_path))
        self._write_json(self.path, data)
        return data

    def save(self) -> None:
        self._write_json(self.path, self.data)

    def viewer_name(self) -> str:
        return str(self.data["viewer"].get("name", "")).strip()

    def set_viewer_name(self, name: str) -> None:
        name = name.strip()[:24]
        if not name:
            return
        old = self.viewer_name()
        if old and old != name:
            self._append_unique(self.data["viewer"]["aliases"], old, 12)
        self.data["viewer"]["name"] = name

    def add_like(self, value: str) -> None:
        self._append_unique(self.data["viewer"]["likes"], value.strip()[:80], 30)

    def add_dislike(self, value: str) -> None:
        self._append_unique(self.data["viewer"]["dislikes"], value.strip()[:80], 30)

    def add_improvement(self, note: str) -> None:
        item = {
            "time": self._now(),
            "note": note.strip()[:160],
        }
        if item["note"]:
            self.data["self"]["improvement_notes"].append(item)
            self.data["self"]["improvement_notes"] = self.data["self"]["improvement_notes"][-40:]

    def record_turn(self, user_text: str, reply: str, intent: str, route: str, topic: str = "") -> None:
        turn = {
            "time": self._now(),
            "user": user_text[:240],
            "reply": reply[:240],
            "intent": intent,
            "route": route,
            "topic": topic,
        }
        conversation = self.data["conversation"]
        conversation["turns"].append(turn)
        conversation["turns"] = conversation["turns"][-24:]
        if topic:
            conversation["current_topic"] = topic

        stats = self.data["stats"]
        stats["total_turns"] = int(stats.get("total_turns", 0)) + 1
        if route == "fast":
            stats["fast_turns"] = int(stats.get("fast_turns", 0)) + 1
        elif route == "llm":
            stats["llm_turns"] = int(stats.get("llm_turns", 0)) + 1
        self.save()

    def prompt_summary(self) -> str:
        viewer = self.data["viewer"]
        chunks = []
        if viewer.get("name"):
            chunks.append(f"用户名字={viewer['name']}")
        if viewer.get("likes"):
            chunks.append("用户喜欢=" + "、".join(viewer["likes"][-5:]))
        if viewer.get("dislikes"):
            chunks.append("用户不喜欢=" + "、".join(viewer["dislikes"][-5:]))

        notes = [item.get("note", "") for item in self.data["self"].get("improvement_notes", [])[-5:]]
        if notes:
            chunks.append("近期改进=" + "；".join(note for note in notes if note))

        recent = self.data["conversation"].get("turns", [])[-4:]
        if recent:
            chunks.append(
                "最近对话="
                + " | ".join(f"用户:{item.get('user', '')} / Mika:{item.get('reply', '')}" for item in recent)
            )
        return "\n".join(chunks) if chunks else "暂无稳定记忆"

    def short_summary(self) -> str:
        viewer = self.data["viewer"]
        stats = self.data["stats"]
        name = viewer.get("name") or "unknown"
        likes = len(viewer.get("likes", []))
        notes = len(self.data["self"].get("improvement_notes", []))
        return (
            f"name={name}, likes={likes}, improvements={notes}, "
            f"turns={stats.get('total_turns', 0)}, fast={stats.get('fast_turns', 0)}, llm={stats.get('llm_turns', 0)}"
        )

    def _import_legacy(self, data: dict[str, Any], legacy: dict[str, Any]) -> None:
        profile = legacy.get("viewer_profile", {})
        if isinstance(profile, dict):
            name = str(profile.get("name", "")).strip()
            if name:
                data["viewer"]["name"] = name[:24]
            for value in profile.get("likes", []) or []:
                self._append_unique(data["viewer"]["likes"], str(value), 30)
            for value in profile.get("dislikes", []) or []:
                self._append_unique(data["viewer"]["dislikes"], str(value), 30)

        for item in legacy.get("model_written_memories", []) or []:
            if not isinstance(item, dict):
                continue
            memory_type = item.get("type", "")
            value = str(item.get("value", "")).strip()
            if not value:
                continue
            if memory_type == "viewer_name" and not data["viewer"]["name"]:
                data["viewer"]["name"] = value[:24]
            elif memory_type == "viewer_preference":
                self._append_unique(data["viewer"]["likes"], value, 30)
            elif memory_type == "viewer_dislike":
                self._append_unique(data["viewer"]["dislikes"], value, 30)

    def _normalize(self, data: dict[str, Any]) -> dict[str, Any]:
        base = deepcopy(DEFAULT_MEMORY)
        if not isinstance(data, dict):
            return base
        self._deep_update(base, data)
        return base

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    @staticmethod
    def _write_json(path: Path, data: dict[str, Any]) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _append_unique(values: list[str], value: str, limit: int) -> None:
        value = value.strip()
        if not value:
            return
        if value in values:
            values.remove(value)
        values.append(value)
        del values[:-limit]

    @staticmethod
    def _deep_update(target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                MemoryStore._deep_update(target[key], value)
            else:
                target[key] = value

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")
