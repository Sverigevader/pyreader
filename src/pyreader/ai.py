from __future__ import annotations

from typing import Protocol


class AIProvider(Protocol):
    def answer(self, question: str, context: str) -> str:
        ...


class NoopProvider:
    def answer(self, question: str, context: str) -> str:
        return (
            "No AI provider configured yet. "
            "Implement AIProvider.answer(question, context) and wire it in cli.py."
        )
