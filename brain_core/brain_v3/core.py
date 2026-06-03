from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from brain.ollama_client import OllamaClient, OllamaConfig
from brain_v2.model_selector import resolve_ollama_models

from .memory import MemoryStore
from .responder import Responder
from .router import Route, Router


@dataclass
class BrainV3Result:
    reply: str
    intent: str
    route: str
    topic: str
    model: str
    memory_summary: str


class BrainV3:
    def __init__(self, data_dir: Path, llm_mode: str = "ollama", model: str = "qwen2.5:3b") -> None:
        self.data_dir = Path(data_dir)
        self.llm_mode = llm_mode
        self.memory = MemoryStore(self.data_dir)
        self.router = Router()

        self.model_name = "off"
        ollama = None
        if llm_mode != "off":
            selection = resolve_ollama_models(model, model)
            self.model_name = selection.chat_model
            ollama = OllamaClient(
                OllamaConfig(
                    model=self.model_name,
                    timeout_seconds=self._timeout_for_model(self.model_name),
                    temperature=0.55,
                    top_p=0.86,
                    num_predict=110,
                )
            )

        self.responder = Responder(self.memory, ollama=ollama, llm_enabled=llm_mode != "off")

    def process(self, user_text: str) -> BrainV3Result:
        user_text = user_text.strip()
        route = self.router.route(user_text)
        reply, used_route = self.responder.respond(user_text, route)
        self.memory.record_turn(
            user_text=user_text,
            reply=reply,
            intent=route.intent,
            route=used_route,
            topic=route.topic,
        )
        return BrainV3Result(
            reply=reply,
            intent=route.intent,
            route=used_route,
            topic=route.topic,
            model=self.model_name if used_route == "llm" else "fast_brain",
            memory_summary=self.memory.short_summary(),
        )

    @staticmethod
    def _timeout_for_model(model: str) -> float:
        lowered = model.lower()
        if "qwen3:0.6b" in lowered or "qwen3:1.7b" in lowered:
            return 18.0
        if "qwen2.5:7b" in lowered or "qwen3:8b" in lowered:
            return 75.0
        if "qwen" in lowered:
            return 45.0
        return 24.0
