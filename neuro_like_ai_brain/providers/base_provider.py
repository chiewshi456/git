from __future__ import annotations

from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_reply(self, context: dict) -> str:
        """Generate one streamer-style reply from the current brain context."""
