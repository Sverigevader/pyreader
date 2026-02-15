import os

from pyreader.cli import _compute_next_offset, _render_chapter, run_reader
from pyreader.epub import EpubBook
from pyreader.models import BookMeta, Chapter


def _make_book(chapter_text: str) -> EpubBook:
    return EpubBook(
        meta=BookMeta(title="T", creator="C", language="en"),
        chapters=[
            Chapter(
                id="c1",
                title="Chapter 1",
                href="chapter1.xhtml",
                text=chapter_text,
            )
        ],
    )


def test_compute_next_offset_supports_line_and_half_page_navigation() -> None:
    assert _compute_next_offset(offset=0, key="down", line_count=20, page_lines=8) == 1
    assert _compute_next_offset(offset=1, key="up", line_count=20, page_lines=8) == 0
    assert _compute_next_offset(offset=0, key="half_down", line_count=20, page_lines=8) == 4
    assert _compute_next_offset(offset=8, key="half_up", line_count=20, page_lines=8) == 4


def test_compute_next_offset_clamps_to_bounds() -> None:
    assert _compute_next_offset(offset=0, key="up", line_count=12, page_lines=8) == 0
    assert _compute_next_offset(offset=4, key="down", line_count=12, page_lines=8) == 4
    assert _compute_next_offset(offset=4, key="half_down", line_count=12, page_lines=8) == 4
    assert _compute_next_offset(offset=0, key="half_up", line_count=12, page_lines=8) == 0


def test_render_chapter_reacts_to_keys(monkeypatch, capsys) -> None:
    book = _make_book("\n".join(f"line {i}" for i in range(1, 13)))

    monkeypatch.setattr(
        "pyreader.cli.shutil.get_terminal_size",
        lambda fallback: os.terminal_size((80, 10)),
    )

    keys = iter(["half_down", "half_down", "half_down", "quit"])
    _render_chapter(book, 0, key_reader=lambda: next(keys), clear_screen=False)
    out = capsys.readouterr().out

    assert "line 1" in out
    assert "line 10" in out
    assert "Keys: ↑/↓ or j/k line  d/u half-page  q quit" in out


class _RecorderAI:
    def __init__(self) -> None:
        self.contexts: list[str] = []
        self.questions: list[str] = []

    def answer(self, question: str, context: str) -> str:
        self.questions.append(question)
        self.contexts.append(context)
        return "answer-ok"


def test_ask_uses_last_visible_viewport(monkeypatch, capsys) -> None:
    book = _make_book("\n".join(f"line {i}" for i in range(1, 30)))
    ai = _RecorderAI()

    commands = iter(["read 1", "ask what happened?", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(commands))
    monkeypatch.setattr("pyreader.cli._render_chapter", lambda *args, **kwargs: "VISIBLE-TEXT")

    run_reader(book, ai)  # type: ignore[arg-type]
    out = capsys.readouterr().out

    assert ai.questions == ["what happened?"]
    assert ai.contexts == ["VISIBLE-TEXT"]
    assert "answer-ok" in out
