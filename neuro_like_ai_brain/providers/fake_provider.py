from __future__ import annotations

from brain.reply import ReplyGenerator

from .base_provider import BaseAIProvider


class FakeAIProvider(BaseAIProvider):
    def __init__(self, reply_generator: ReplyGenerator | None = None) -> None:
        self.reply_generator = reply_generator or ReplyGenerator()

    def generate_reply(self, context: dict) -> str:
        return self.reply_generator.generate(context)
