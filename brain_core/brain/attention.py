from __future__ import annotations


class AttentionSystem:
    INTENT_TARGETS = {
        "gift": "gift_event",
        "insult": "conflict",
        "emotional_support": "viewer_emotion",
        "personal_question": "personal_identity",
        "silence": "chat_silence",
        "praise": "praise",
        "encourage": "relationship",
        "question": "topic_question",
    }

    def select(
        self,
        intent: str,
        emotion: str,
        memory: dict,
        drives: list[dict],
    ) -> str:
        if intent in self.INTENT_TARGETS:
            return self.INTENT_TARGETS[intent]

        top_drive = drives[0]["name"] if drives else ""
        if top_drive == "wants_attention":
            return "self_status"
        if top_drive == "wants_to_learn_about_viewer":
            return "viewer_message"

        if emotion in {"hurt", "annoyed"}:
            return "conflict"
        if emotion in {"lonely", "tired", "nervous"}:
            return "self_status"

        if memory.get("relationship_level") in {"regular", "close"}:
            return "relationship"

        return "viewer_message"
