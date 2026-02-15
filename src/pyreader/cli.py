from __future__ import annotations

import argparse
import shutil
import sys
import textwrap
from collections.abc import Callable

try:
    import readline
except ImportError:  # pragma: no cover - platform dependent
    readline = None  # type: ignore[assignment]

try:
    import termios
    import tty
except ImportError:  # pragma: no cover - platform dependent
    termios = None  # type: ignore[assignment]
    tty = None  # type: ignore[assignment]

from .ai import AIProvider, NoopProvider
from .epub import EpubBook, load_epub
from .providers import OpenAICompatibleProvider

DISPLAY_WIDTH = 80
DISPLAY_HEIGHT = 24
VIEWPORT_RESERVED_LINES = 5


KeyReader = Callable[[], str]


def _print_help() -> None:
    print(
        textwrap.dedent(
            """
            Commands:
              help                 Show this help
              meta                 Show book metadata
              chapters             List chapters
              read <n>             Read chapter number n (interactive)
              next                 Read next chapter
              prev                 Read previous chapter
              search <query>       Search in chapter text
              ask <question>       Ask AI using currently visible text
              quit / exit          Leave reader
            """
        ).strip()
    )


def _wrap_text(text: str, width: int) -> str:
    wrapped_paragraphs: list[str] = []
    for paragraph in text.split("\n"):
        if not paragraph.strip():
            wrapped_paragraphs.append("")
        else:
            wrapped_paragraphs.append(
                textwrap.fill(paragraph.strip(), width=width, replace_whitespace=True)
            )
    return "\n".join(wrapped_paragraphs)


def _read_key() -> str:
    if termios is None or tty is None:
        return input().strip().lower()

    fd = sys.stdin.fileno()
    original = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key == "\x1b":
            maybe_bracket = sys.stdin.read(1)
            if maybe_bracket != "[":
                return "escape"
            code = sys.stdin.read(1)
            if code == "A":
                return "up"
            if code == "B":
                return "down"
            return "escape"
        if key in {"\x03", "\x11"}:
            return "quit"
        if key == "j":
            return "down"
        if key == "k":
            return "up"
        if key == "d":
            return "half_down"
        if key == "u":
            return "half_up"
        if key == "q":
            return "quit"
        return key
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, original)


def _compute_next_offset(offset: int, key: str, line_count: int, page_lines: int) -> int:
    max_offset = max(0, line_count - page_lines)
    half_page = max(1, page_lines // 2)
    if key == "up":
        return max(0, offset - 1)
    if key == "down":
        return min(max_offset, offset + 1)
    if key == "half_up":
        return max(0, offset - half_page)
    if key == "half_down":
        return min(max_offset, offset + half_page)
    return offset


def _render_chapter(
    book: EpubBook,
    idx: int,
    *,
    key_reader: KeyReader | None = None,
    clear_screen: bool = True,
) -> str:
    key_reader = key_reader or _read_key
    term = shutil.get_terminal_size(fallback=(DISPLAY_WIDTH, DISPLAY_HEIGHT))
    width = max(20, term.columns - 1)
    page_lines = max(5, term.lines - VIEWPORT_RESERVED_LINES)
    chapter = book.chapters[idx]
    print()
    rendered = _wrap_text(chapter.text, width=width)
    lines = rendered.splitlines()
    if not lines:
        lines = [""]
    offset = 0
    max_offset = max(0, len(lines) - page_lines)

    while True:
        if clear_screen:
            print("\x1b[2J\x1b[H", end="")

        visible = lines[offset : offset + page_lines]
        print(f"[{idx + 1}] {chapter.title} ({chapter.href})")
        print(f"Lines {offset + 1}-{offset + len(visible)} of {len(lines)}")
        print("-" * width)
        print("\n".join(visible))
        print("-" * width)
        print("Keys: ↑/↓ or j/k line  d/u half-page  q quit")
        viewport_text = "\n".join(visible)

        key = key_reader()
        if key == "quit":
            return viewport_text
        offset = _compute_next_offset(offset, key, len(lines), page_lines)
        if offset == max_offset and key in {"down", "half_down"}:
            continue


def _initial_viewport_text(book: EpubBook, idx: int) -> str:
    term = shutil.get_terminal_size(fallback=(DISPLAY_WIDTH, DISPLAY_HEIGHT))
    width = max(20, term.columns - 1)
    page_lines = max(5, term.lines - VIEWPORT_RESERVED_LINES)
    rendered = _wrap_text(book.chapters[idx].text, width=width)
    lines = rendered.splitlines()
    if not lines:
        return ""
    return "\n".join(lines[:page_lines])


def run_reader(book: EpubBook, ai: AIProvider) -> None:
    current = 0
    current_viewport_text = _initial_viewport_text(book, current)
    print(f"Loaded: {book.meta.title} by {book.meta.creator}")
    print("Type `help` for commands.")

    while True:
        raw = input("\npyreader> ").strip()
        if not raw:
            continue
        if readline is not None:
            readline.add_history(raw)

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in {"quit", "exit"}:
            break
        if cmd == "help":
            _print_help()
            continue
        if cmd == "meta":
            print(f"Title: {book.meta.title}")
            print(f"Creator: {book.meta.creator}")
            print(f"Language: {book.meta.language or 'unknown'}")
            continue
        if cmd == "chapters":
            for i, ch in enumerate(book.chapters, start=1):
                print(f"{i:>3}. {ch.title} [{ch.href}]")
            continue
        if cmd == "read":
            if not arg.isdigit():
                print("Usage: read <chapter_number>")
                continue
            n = int(arg) - 1
            if not (0 <= n < len(book.chapters)):
                print("Chapter out of range")
                continue
            current = n
            current_viewport_text = _render_chapter(book, current)
            continue
        if cmd == "next":
            if current < len(book.chapters) - 1:
                current += 1
            current_viewport_text = _render_chapter(book, current)
            continue
        if cmd == "prev":
            if current > 0:
                current -= 1
            current_viewport_text = _render_chapter(book, current)
            continue
        if cmd == "search":
            if not arg:
                print("Usage: search <query>")
                continue
            q = arg.lower()
            for i, ch in enumerate(book.chapters, start=1):
                if q in ch.text.lower():
                    print(f"match: chapter {i} ({ch.href})")
            continue
        if cmd == "ask":
            if not arg:
                print("Usage: ask <question>")
                continue
            context = current_viewport_text
            answer = ai.answer(arg, context)
            print(answer)
            continue

        print(f"Unknown command: {cmd}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read EPUB books in terminal")
    parser.add_argument("epub_path", help="Path to .epub file")
    parser.add_argument(
        "--ai-provider",
        default="noop",
        choices=["noop", "openai"],
        help="AI backend to use for `ask` command",
    )
    parser.add_argument(
        "--ai-model",
        default="gpt-4o-mini",
        help="Model name when using --ai-provider openai",
    )
    parser.add_argument(
        "--ai-base-url",
        default="https://api.openai.com/v1",
        help="Base URL for OpenAI API",
    )
    args = parser.parse_args()

    book = load_epub(args.epub_path)
    if args.ai_provider == "openai":
        ai: AIProvider = OpenAICompatibleProvider(
            model=args.ai_model,
            base_url=args.ai_base_url,
        )
    else:
        ai = NoopProvider()
    run_reader(book, ai)


if __name__ == "__main__":
    main()
