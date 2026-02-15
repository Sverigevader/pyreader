from __future__ import annotations

import argparse
import textwrap

from .ai import AIProvider, NoopProvider
from .epub import EpubBook, load_epub
from .providers import OpenAICompatibleProvider

DISPLAY_WIDTH = 80


def _print_help() -> None:
    print(
        textwrap.dedent(
            """
            Commands:
              help                 Show this help
              meta                 Show book metadata
              chapters             List chapters
              read <n>             Read chapter number n
              next                 Read next chapter
              prev                 Read previous chapter
              search <query>       Search in chapter text
              ask <question>       Ask AI using current chapter as context
              quit / exit          Leave reader
            """
        ).strip()
    )


def _render_chapter(book: EpubBook, idx: int) -> None:
    def wrap_text(text: str, width: int = DISPLAY_WIDTH) -> str:
        wrapped_paragraphs: list[str] = []
        for paragraph in text.split("\n"):
            if not paragraph.strip():
                wrapped_paragraphs.append("")
            else:
                wrapped_paragraphs.append(
                    textwrap.fill(paragraph.strip(), width=width, replace_whitespace=True)
                )
        return "\n".join(wrapped_paragraphs)

    chapter = book.chapters[idx]
    print(f"\n[{idx + 1}] {chapter.title} ({chapter.href})\n")
    preview = chapter.text[:4000]
    rendered = wrap_text(preview)
    print(rendered + ("\n..." if len(chapter.text) > 4000 else ""))


def run_reader(book: EpubBook, ai: AIProvider) -> None:
    current = 0
    print(f"Loaded: {book.meta.title} by {book.meta.creator}")
    print("Type `help` for commands.")

    while True:
        raw = input("\npyreader> ").strip()
        if not raw:
            continue

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
            _render_chapter(book, current)
            continue
        if cmd == "next":
            if current < len(book.chapters) - 1:
                current += 1
            _render_chapter(book, current)
            continue
        if cmd == "prev":
            if current > 0:
                current -= 1
            _render_chapter(book, current)
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
            context = book.chapters[current].text[:12000]
            print(ai.answer(arg, context))
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
        help="Base URL for OpenAI-compatible API",
    )
    args = parser.parse_args()

    book = load_epub(args.epub_path)
    if args.ai_provider == "openai":
        ai: AIProvider = OpenAICompatibleProvider(model=args.ai_model, base_url=args.ai_base_url)
    else:
        ai = NoopProvider()
    run_reader(book, ai)


if __name__ == "__main__":
    main()
