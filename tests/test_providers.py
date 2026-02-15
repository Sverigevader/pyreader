import json

from pyreader.providers import OpenAICompatibleProvider


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_openai_provider_uses_custom_path_and_optional_auth(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(req, timeout: int):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _FakeResponse(
            {"choices": [{"message": {"content": "ok"}}]}
        )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("pyreader.providers.request.urlopen", fake_urlopen)

    provider = OpenAICompatibleProvider(
        model="gpt-4o-mini",
        base_url="https://example.test/api",
        chat_path="v2/chat",
        system_prompt="Use only provided text.",
    )
    answer = provider.answer("Q?", "C")

    assert answer == "ok"
    assert captured["url"] == "https://example.test/api/v2/chat"
    headers = captured["headers"]
    assert "Authorization" not in headers
    assert headers["Content-type"] == "application/json"
    body = captured["body"]
    assert body["messages"][0]["content"] == "Use only provided text."
    assert captured["timeout"] == 30

