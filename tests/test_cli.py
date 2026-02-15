import os

from pyreader.cli import _render_chapter
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


def test_render_chapter_paginates_by_terminal_height(monkeypatch, capsys) -> None:
    book = _make_book("\n".join(f"line {i}" for i in range(1, 8)))
    prompts: list[str] = []

    monkeypatch.setattr("pyreader.cli.shutil.get_terminal_size", lambda fallback: os.terminal_size((80, 8)))

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    monkeypatch.setattr("builtins.input", fake_input)

    _render_chapter(book, 0)
    out = capsys.readouterr().out

    assert "line 1" in out
    assert "line 7" in out
    assert prompts == ["--More-- [Enter=next, q=quit] "]


def test_render_chapter_quit_stops_after_first_page(monkeypatch, capsys) -> None:
    book = _make_book("\n".join(f"line {i}" for i in range(1, 15)))
    prompts: list[str] = []

    monkeypatch.setattr("pyreader.cli.shutil.get_terminal_size", lambda fallback: os.terminal_size((80, 8)))

    def fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return "q"

    monkeypatch.setattr("builtins.input", fake_input)

    _render_chapter(book, 0)
    out = capsys.readouterr().out

    assert "line 1" in out
    assert "line 6" in out
    assert "line 7" not in out
    assert len(prompts) == 1
