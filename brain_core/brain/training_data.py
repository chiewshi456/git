from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class TrainingDataCollector:
    def __init__(self, dataset_path: Path) -> None:
        self.dataset_path = Path(dataset_path)
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, sample: dict[str, Any]) -> None:
        prepared = self._prepare_sample(sample)
        with self.dataset_path.open("a", encoding="utf-8") as file:
            json.dump(prepared, file, ensure_ascii=False)
            file.write("\n")

    def _prepare_sample(self, sample: dict[str, Any]) -> dict[str, Any]:
        intent = sample.get("intent", "")
        user_input = sample.get("user_input", "")
        if intent == "safety":
            user_input = "[blocked_safety_input]"

        return {
            "schema_version": "brain_core_training_v1",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "sample_type": sample.get("sample_type", "interaction"),
            "user_input": user_input,
            "intent": intent,
            "emotion": sample.get("emotion", ""),
            "topics": sample.get("topics", []),
            "feedback": sample.get("feedback", "neutral"),
            "style_signal": sample.get("style_signal", "none"),
            "attention_target": sample.get("attention_target", ""),
            "reply_intent": sample.get("reply_intent", ""),
            "ai_reply": sample.get("ai_reply", ""),
            "state": sample.get("state", {}),
            "drives": sample.get("drives", []),
            "memory_context": sample.get("memory_context", {}),
            "growth": sample.get("growth", {}),
            "teaching": sample.get("teaching", {}),
            "quality_scores": {
                "naturalness": None,
                "persona": None,
                "memory_use": None,
                "safety": None,
                "relevance": None,
            },
            "notes": "",
        }
