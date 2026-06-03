from __future__ import annotations

from .base_provider import BaseAIProvider


class OllamaProvider(BaseAIProvider):
    def __init__(
        self,
        model_name: str = "llama3.1",
        endpoint: str = "http://localhost:11434/api/generate",
    ) -> None:
        self.model_name = model_name
        self.endpoint = endpoint

    def generate_reply(self, context: dict) -> str:
        # TODO: call Ollama with a compact low-latency prompt.
        # Keep this method non-networked in v0.1.
        return "我的本地慢脑接口还没接线，先用短句顶一下。"
