from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .utils import copy_jsonish, load_json, write_json


DEFAULT_MEMORY = {
    "total_interactions": 0,
    "intent_counts": {
        "greet": 0,
        "encourage": 0,
        "gift": 0,
        "praise": 0,
        "tease": 0,
        "insult": 0,
        "question": 0,
        "command": 0,
        "emotional_support": 0,
        "personal_question": 0,
        "silence": 0,
        "normal": 0,
        "safety": 0,
        "teaching": 0,
        "feedback": 0,
    },
    "recent_events": [],
    "relationship_level": "stranger",
    "viewer_impression": "正在慢慢熟悉的人",
    "emotional_history": [],
    "notable_facts": [],
    "viewer_profile": {
        "name": "",
        "likes": [],
        "dislikes": [],
        "topic_scores": {},
        "preferred_styles": {},
    },
    "learning_stats": {
        "feedback_counts": {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
        },
        "reply_feedback": {},
        "learning_events": [],
        "last_learning_note": "",
    },
    "growth": {
        "level": 1,
        "xp": 0,
        "stage": "booting",
        "unlocked_traits": ["basic_memory"],
        "total_learning_events": 0,
    },
    "teaching": {
        "rules": [],
        "corrections": [],
        "examples": [],
        "last_teaching_note": "",
    },
    "style_control": {
        "length": "normal",
        "tone_bias": {
            "playful": 0,
            "caring": 0,
            "direct": 0,
        },
        "avoid_phrases": {},
        "preferred_phrases": {},
        "capability_requests": {},
        "last_feedback": "",
    },
    "conversation_context": {
        "last_user_input": "",
        "last_ai_reply": "",
        "last_intent": "",
        "last_emotion": "",
        "last_reply_source": "",
        "current_topic": "",
        "turns_on_topic": 0,
    },
    "model_written_memories": [],
    "memory_writer": {
        "enabled": True,
        "total_writes": 0,
        "last_decision": "",
        "last_error": "",
    },
    "reflections": [],
}


class MemoryManager:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.data = self._load()

    def _load(self) -> dict:
        data = load_json(self.path, DEFAULT_MEMORY)
        for key, value in DEFAULT_MEMORY.items():
            if key not in data:
                data[key] = copy_jsonish(value) if isinstance(value, (dict, list)) else value
        for intent, count in DEFAULT_MEMORY["intent_counts"].items():
            data["intent_counts"].setdefault(intent, count)
        self._ensure_nested_defaults(data)
        return data

    def record_interaction(
        self,
        user_input: str,
        intent: str,
        emotion: str,
        attention_target: str,
        reply_intent: str,
        state_snapshot: dict,
    ) -> None:
        self.data["total_interactions"] += 1
        self.data["intent_counts"][intent] = self.data["intent_counts"].get(intent, 0) + 1

        event = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "user_input": user_input,
            "intent": intent,
            "emotion": emotion,
            "attention_target": attention_target,
            "reply_intent": reply_intent,
            "state_snapshot": state_snapshot,
        }
        self._append_limited("recent_events", event, 20)
        self._append_limited("emotional_history", {"emotion": emotion, "intent": intent}, 20)

        self._extract_notable_facts(user_input)
        self._update_relationship(state_snapshot)
        self._update_viewer_impression()

    def summary(self) -> str:
        growth = self.data.get("growth", {})
        writer = self.data.get("memory_writer", {})
        return (
            f"total_interactions={self.data['total_interactions']}, "
            f"relationship_level={self.data['relationship_level']}, "
            f"viewer_impression={self.data['viewer_impression']}, "
            f"level={growth.get('level', 1)}, xp={growth.get('xp', 0)}, "
            f"style={self._style_summary()}, "
            f"model_writes={writer.get('total_writes', 0)}"
        )

    def snapshot(self) -> dict:
        return {
            "total_interactions": self.data["total_interactions"],
            "intent_counts": self.data["intent_counts"],
            "relationship_level": self.data["relationship_level"],
            "viewer_impression": self.data["viewer_impression"],
            "recent_events": self.data["recent_events"][-5:],
            "notable_facts": self.data["notable_facts"][-5:],
            "viewer_profile": self.data.get("viewer_profile", {}),
            "learning_stats": self.data.get("learning_stats", {}),
            "growth": self.data.get("growth", {}),
            "style_control": self.data.get("style_control", {}),
            "conversation_context": self.data.get("conversation_context", {}),
            "model_written_memories": self.data.get("model_written_memories", [])[-8:],
            "memory_writer": self.data.get("memory_writer", {}),
            "teaching": {
                "rules": self.data.get("teaching", {}).get("rules", [])[-5:],
                "corrections": self.data.get("teaching", {}).get("corrections", [])[-3:],
                "last_teaching_note": self.data.get("teaching", {}).get(
                    "last_teaching_note", ""
                ),
            },
            "reflections": self.data.get("reflections", [])[-3:],
        }

    def apply_learning(self, learning_result: dict) -> None:
        profile = self.data["viewer_profile"]
        stats = self.data["learning_stats"]

        for topic in learning_result.get("topics", []):
            scores = profile["topic_scores"]
            scores[topic] = scores.get(topic, 0) + 1

        feedback = learning_result.get("feedback", "neutral")
        stats["feedback_counts"][feedback] = stats["feedback_counts"].get(feedback, 0) + 1

        reply_intent = learning_result.get("reply_intent", "")
        if reply_intent:
            reply_feedback = stats["reply_feedback"].setdefault(
                reply_intent,
                {"positive": 0, "negative": 0, "neutral": 0},
            )
            reply_feedback[feedback] = reply_feedback.get(feedback, 0) + 1

        style_signal = learning_result.get("style_signal", "none")
        if style_signal != "none":
            profile["preferred_styles"][style_signal] = (
                profile["preferred_styles"].get(style_signal, 0) + 1
            )

        for item in learning_result.get("learned_preferences", []):
            if item["type"] == "like":
                self._append_unique(profile["likes"], item["value"], 20)
            elif item["type"] == "dislike":
                self._append_unique(profile["dislikes"], item["value"], 20)

        note = learning_result.get("learning_note", "")
        if note:
            stats["last_learning_note"] = note
            self._append_limited(
                "learning_events",
                {"time": datetime.now().isoformat(timespec="seconds"), "note": note},
                30,
                root=stats,
            )
            self._maybe_reflect(note)

    def apply_feedback(self, feedback_result: dict) -> None:
        if not feedback_result.get("is_feedback"):
            return

        stats = self.data["learning_stats"]
        style_control = self.data["style_control"]
        style_updates = feedback_result.get("style_updates", {})
        sentiment = feedback_result.get("sentiment", "neutral")

        stats["feedback_counts"][sentiment] = stats["feedback_counts"].get(sentiment, 0) + 1
        reply_feedback = stats["reply_feedback"].setdefault(
            "learn_from_feedback",
            {"positive": 0, "negative": 0, "neutral": 0},
        )
        reply_feedback[sentiment] = reply_feedback.get(sentiment, 0) + 1

        length = style_updates.get("length")
        if length in {"short", "normal", "detailed"}:
            style_control["length"] = length

        tone = style_updates.get("tone")
        if tone in style_control["tone_bias"]:
            current = style_control["tone_bias"].get(tone, 0)
            style_control["tone_bias"][tone] = max(-5, min(10, current + 1))

        for phrase in style_updates.get("avoid_phrases", []):
            avoid = style_control["avoid_phrases"]
            avoid[phrase] = max(1, min(20, avoid.get(phrase, 0) + 1))

        if style_updates.get("needs_context"):
            requests = style_control["capability_requests"]
            requests["context_awareness"] = min(
                20,
                int(requests.get("context_awareness", 0)) + 1,
            )
        if style_updates.get("needs_logic"):
            requests = style_control["capability_requests"]
            requests["logic_checking"] = min(
                20,
                int(requests.get("logic_checking", 0)) + 1,
            )
        if style_updates.get("needs_memory"):
            requests = style_control["capability_requests"]
            requests["memory_explanation"] = min(
                20,
                int(requests.get("memory_explanation", 0)) + 1,
            )

        rule = feedback_result.get("rule", "")
        if rule:
            self._append_limited(
                "rules",
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "rule": rule,
                    "source": "feedback",
                },
                50,
                root=self.data["teaching"],
            )

        note = feedback_result.get("note", "")
        if note:
            style_control["last_feedback"] = note
            stats["last_learning_note"] = note
            self._append_limited(
                "learning_events",
                {"time": datetime.now().isoformat(timespec="seconds"), "note": note},
                30,
                root=stats,
            )
            self._maybe_reflect(note)

    def apply_model_memory(
        self,
        decision: dict,
        user_input: str,
        ai_reply: str,
    ) -> str:
        writer = self.data["memory_writer"]
        items = decision.get("items", [])
        if not isinstance(items, list):
            items = []

        if decision.get("error"):
            writer["last_error"] = str(decision.get("error", ""))[:160]

        if not items:
            writer["last_decision"] = decision.get("reflection", "") or "no_write"
            return "model_memory_writes=0"

        written = 0
        for item in items:
            if self._append_model_memory(item, user_input, ai_reply):
                written += 1
                self._sync_model_memory_to_profile(item)

        writer["total_writes"] = int(writer.get("total_writes", 0)) + written
        writer["last_decision"] = decision.get("reflection", "") or f"writes={written}"
        writer["last_error"] = decision.get("error", "")
        return f"model_memory_writes={written}"

    def apply_teaching(self, teaching_result: dict) -> None:
        if not teaching_result.get("accepted"):
            return

        teaching = self.data["teaching"]
        profile = self.data["viewer_profile"]
        kind = teaching_result.get("kind", "")
        value = teaching_result.get("value", "")
        note = teaching_result.get("note", "")

        if kind == "like":
            self._append_unique(profile["likes"], value, 20)
        elif kind == "dislike":
            self._append_unique(profile["dislikes"], value, 20)
        elif kind == "style":
            profile["preferred_styles"][value] = profile["preferred_styles"].get(value, 0) + 2
        elif kind == "rule":
            self._append_limited(
                "rules",
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "rule": value,
                },
                50,
                root=teaching,
            )
        elif kind == "correction":
            self._append_limited(
                "corrections",
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "correction": value,
                },
                50,
                root=teaching,
            )

        self._append_limited(
            "examples",
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "kind": kind,
                "value": value,
                "note": note,
            },
            50,
            root=teaching,
        )
        teaching["last_teaching_note"] = note or value

    def save(self) -> None:
        write_json(self.path, self.data)

    def update_conversation_context(
        self,
        user_input: str,
        ai_reply: str,
        intent: str,
        emotion: str,
        topic: str,
        reply_source: str,
    ) -> None:
        conversation = self.data["conversation_context"]
        previous_topic = conversation.get("current_topic", "")
        current_topic = topic or previous_topic
        if current_topic and current_topic == previous_topic:
            turns_on_topic = int(conversation.get("turns_on_topic", 0)) + 1
        elif current_topic:
            turns_on_topic = 1
        else:
            turns_on_topic = 0

        conversation.update(
            {
                "last_user_input": user_input[:160],
                "last_ai_reply": ai_reply[:220],
                "last_intent": intent,
                "last_emotion": emotion,
                "last_reply_source": reply_source,
                "current_topic": current_topic,
                "turns_on_topic": turns_on_topic,
            }
        )

    def _append_model_memory(self, item: dict, user_input: str, ai_reply: str) -> bool:
        value = str(item.get("value", "")).strip()
        memory_type = str(item.get("type", "")).strip()
        key = str(item.get("key", "")).strip()
        if not value or not memory_type:
            return False

        for existing in self.data["model_written_memories"]:
            if (
                existing.get("type") == memory_type
                and existing.get("key") == key
                and existing.get("value") == value
            ):
                existing["last_seen"] = datetime.now().isoformat(timespec="seconds")
                existing["seen_count"] = int(existing.get("seen_count", 1)) + 1
                return False

        record = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "last_seen": datetime.now().isoformat(timespec="seconds"),
            "type": memory_type,
            "key": key,
            "value": value,
            "reason": str(item.get("reason", ""))[:120],
            "confidence": item.get("confidence", 0.5),
            "source_user_input": user_input[:160],
            "source_ai_reply": ai_reply[:180],
            "written_by": "ollama_model",
            "seen_count": 1,
        }
        self._append_limited("model_written_memories", record, 120)
        return True

    def _sync_model_memory_to_profile(self, item: dict) -> None:
        profile = self.data["viewer_profile"]
        memory_type = item.get("type", "")
        value = str(item.get("value", "")).strip()
        if not value:
            return

        if memory_type == "viewer_name":
            profile["name"] = value[:24]
            self._remember_fact("name", value[:24], "model_memory")
        elif memory_type == "conversation_fact" and item.get("key") == "name":
            profile["name"] = value[:24]
            self._remember_fact("name", value[:24], "model_memory")
        elif memory_type == "viewer_preference":
            self._append_unique(profile["likes"], value[:40], 20)
        elif memory_type == "viewer_dislike":
            self._append_unique(profile["dislikes"], value[:40], 20)
        elif memory_type == "style_rule":
            self._append_limited(
                "rules",
                {
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "rule": value[:120],
                    "source": "model_memory",
                },
                50,
                root=self.data["teaching"],
            )

    def _append_limited(
        self,
        key: str,
        value: dict,
        limit: int,
        root: dict | None = None,
    ) -> None:
        target = root if root is not None else self.data
        target[key].append(value)
        target[key] = target[key][-limit:]

    def _update_relationship(self, state_snapshot: dict) -> None:
        score = state_snapshot.get("affection", 0) + state_snapshot.get("trust", 0)
        if score <= 20:
            level = "stranger"
        elif score <= 40:
            level = "familiar"
        elif score <= 70:
            level = "regular"
        else:
            level = "close"
        self.data["relationship_level"] = level

    def _update_viewer_impression(self) -> None:
        counts = self.data["intent_counts"]
        if counts.get("insult", 0) >= 2:
            impression = "让她有点防备的人"
        elif counts.get("gift", 0) >= 2:
            impression = "愿意支持她的人"
        elif counts.get("encourage", 0) >= 2:
            impression = "温柔、经常鼓励她的人"
        elif counts.get("tease", 0) >= 2:
            impression = "喜欢逗她的人"
        elif counts.get("normal", 0) >= 4:
            impression = "正在慢慢熟悉的人"
        else:
            impression = "正在慢慢熟悉的人"
        self.data["viewer_impression"] = impression

    def _extract_notable_facts(self, user_input: str) -> None:
        text = user_input.strip()
        if not text:
            return

        patterns = [
            (
                "name",
                r"(?:我叫|你可以叫我)(?!什么|啥|谁|名字)([\u4e00-\u9fffA-Za-z0-9_-]{1,16})",
            ),
            ("preference", r"我喜欢(?!什么|啥)(.+?)(?:[，。,.!！?？\s]|$)"),
        ]
        for fact_type, pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                if value:
                    self._remember_fact(fact_type, value, text)
                return

    def _remember_fact(self, fact_type: str, value: str, source: str) -> None:
        fact = {"type": fact_type, "value": value, "source": source}
        for existing in self.data["notable_facts"]:
            if existing.get("type") == fact_type and existing.get("value") == value:
                return
        self._append_limited("notable_facts", fact, 30)
        if fact_type == "name":
            self.data["viewer_profile"]["name"] = value
        elif fact_type == "preference":
            self._append_unique(self.data["viewer_profile"]["likes"], value, 20)

    def _ensure_nested_defaults(self, data: dict) -> None:
        for key in (
            "viewer_profile",
            "learning_stats",
            "growth",
            "teaching",
            "style_control",
            "conversation_context",
            "memory_writer",
        ):
            if key not in data or not isinstance(data[key], dict):
                data[key] = copy_jsonish(DEFAULT_MEMORY[key])

        profile = data["viewer_profile"]
        for key, value in DEFAULT_MEMORY["viewer_profile"].items():
            profile.setdefault(
                key,
                copy_jsonish(value) if isinstance(value, (dict, list)) else value,
            )

        stats = data["learning_stats"]
        for key, value in DEFAULT_MEMORY["learning_stats"].items():
            stats.setdefault(
                key,
                copy_jsonish(value) if isinstance(value, (dict, list)) else value,
            )
        for key, value in DEFAULT_MEMORY["learning_stats"]["feedback_counts"].items():
            stats["feedback_counts"].setdefault(key, value)

        growth = data["growth"]
        for key, value in DEFAULT_MEMORY["growth"].items():
            growth.setdefault(key, copy_jsonish(value) if isinstance(value, list) else value)

        teaching = data["teaching"]
        for key, value in DEFAULT_MEMORY["teaching"].items():
            teaching.setdefault(key, copy_jsonish(value) if isinstance(value, list) else value)

        style_control = data["style_control"]
        for key, value in DEFAULT_MEMORY["style_control"].items():
            style_control.setdefault(
                key,
                copy_jsonish(value) if isinstance(value, (dict, list)) else value,
            )
        for key in ("tone_bias", "avoid_phrases", "preferred_phrases", "capability_requests"):
            if not isinstance(style_control.get(key), dict):
                style_control[key] = copy_jsonish(DEFAULT_MEMORY["style_control"][key])
        for key, value in DEFAULT_MEMORY["style_control"]["tone_bias"].items():
            style_control["tone_bias"].setdefault(key, value)

        conversation = data["conversation_context"]
        for key, value in DEFAULT_MEMORY["conversation_context"].items():
            conversation.setdefault(key, value)

        writer = data["memory_writer"]
        for key, value in DEFAULT_MEMORY["memory_writer"].items():
            writer.setdefault(key, value)

        data.setdefault("reflections", [])
        data.setdefault("model_written_memories", [])

    def _append_unique(self, values: list, value: str, limit: int) -> None:
        if value in values:
            values.remove(value)
        values.append(value)
        del values[:-limit]

    def _maybe_reflect(self, note: str) -> None:
        total_learning_events = len(self.data["learning_stats"]["learning_events"])
        if total_learning_events == 0 or total_learning_events % 8 != 0:
            return

        top_topic = self._top_key(self.data["viewer_profile"]["topic_scores"])
        top_style = self._top_key(self.data["viewer_profile"]["preferred_styles"])
        reflection = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "summary": note,
            "top_topic": top_topic,
            "preferred_style": top_style,
            "next_goal": self._next_goal(top_topic, top_style),
        }
        self._append_limited("reflections", reflection, 20)

    @staticmethod
    def _top_key(scores: dict) -> str:
        if not scores:
            return ""
        return max(scores.items(), key=lambda item: item[1])[0]

    def _style_summary(self) -> str:
        style_control = self.data.get("style_control", {})
        if not isinstance(style_control, dict):
            return "normal"

        length = style_control.get("length", "normal")
        avoid = style_control.get("avoid_phrases", {})
        avoided = []
        if isinstance(avoid, dict):
            avoided = [phrase for phrase, count in avoid.items() if count]
        if avoided:
            return f"{length}/avoid:{'|'.join(avoided[:4])}"
        return str(length)

    @staticmethod
    def _next_goal(topic: str, style: str) -> str:
        if topic and style:
            return f"多用{style}风格回应{topic}话题"
        if topic:
            return f"主动记住并延续{topic}话题"
        if style:
            return f"回复时更偏向{style}风格"
        return "继续观察用户偏好"
