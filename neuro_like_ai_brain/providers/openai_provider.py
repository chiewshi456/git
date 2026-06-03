from __future__ import annotations

import os

from .base_provider import BaseAIProvider


class OpenAIProvider(BaseAIProvider):
    def __init__(self, model_name: str = "gpt-4.1-mini", api_key: str | None = None) -> None:
        self.model_name = model_name
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate_reply(self, context: dict) -> str:
        # TODO: call OpenAI Responses API with short context and timeout controls.
        # Keep this method non-networked in v0.1.
        return "我的云端慢脑还没上线，我先别装懂。"
