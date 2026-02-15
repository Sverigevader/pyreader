from __future__ import annotations

import os
from urllib import request
import json

from .ai import AIProvider


class OpenAICompatibleProvider(AIProvider):
    """Minimal OpenAI-compatible HTTP provider.

    Expects:
    - base_url: e.g. https://api.openai.com/v1
    - api_key in env
    - chat completions endpoint at /chat/completions
    """

    def __init__(self, model: str, api_key_env: str = "OPENAI_API_KEY", base_url: str = "https://api.openai.com/v1") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = os.getenv(api_key_env, "")

    def answer(self, question: str, context: str) -> str:
        if not self.api_key:
            return "Missing API key. Set OPENAI_API_KEY (or configure another provider)."

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You answer questions about book text context only."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": 0.2,
        }

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return f"AI request failed: {exc}"
