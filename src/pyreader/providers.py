from __future__ import annotations

import os
from urllib import request
import json

from .ai import AIProvider


class OpenAICompatibleProvider(AIProvider):
    """Minimal OpenAI-compatible HTTP provider.

    Expects:
    - base_url: e.g. https://api.openai.com/v1
    - optional api_key in env
    - configurable chat endpoint path
    """

    def __init__(
        self,
        model: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "https://api.openai.com/v1",
        chat_path: str = "/chat/completions",
        system_prompt: str = "You answer questions about book text context only.",
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        if not chat_path.startswith("/"):
            chat_path = f"/{chat_path}"
        self.chat_path = chat_path
        self.api_key = os.getenv(api_key_env, "")
        self.system_prompt = system_prompt

    def answer(self, question: str, context: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": 0.2,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        req = request.Request(
            url=f"{self.base_url}{self.chat_path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            return f"AI request failed: {exc}"
