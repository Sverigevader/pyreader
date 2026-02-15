# Agent Guide: pyreader

This file helps AI agents navigate and modify `pyreader` safely.

## What This App Does

- Reads EPUB files in a terminal.
- Lets users browse chapters and read with interactive key navigation.
- Supports asking AI questions based on the currently visible text window.
- Keeps a developer-agent collaboration log in the repository.

## Entry Points

- CLI entry: `src/pyreader/cli.py`
- Package script: `pyreader = "pyreader.cli:main"` in `pyproject.toml`

## Core Modules

- `src/pyreader/cli.py`
  - Command loop (`run_reader`)
  - Interactive chapter rendering (`_render_chapter`)
  - Key handling (`_read_key`)
  - AI `ask` command integration
- `src/pyreader/epub.py`
  - EPUB loading and chapter extraction
- `src/pyreader/providers.py`
  - `OpenAICompatibleProvider` HTTP integration
- `src/pyreader/ai.py`
  - `AIProvider` protocol and `NoopProvider`

## Reading UX Model

- `read <n>`, `next`, and `prev` open an interactive viewport.
- Navigation keys:
  - `up/down` arrows or `k/j` for single-line movement
  - `u/d` for half-page movement
  - `q` to exit reader viewport
- The last visible viewport text is saved and used as AI context.

## AI Flow

1. User runs `ask <question>`.
2. CLI sends current viewport text (not full chapter) as `context`.
3. Provider returns full answer.
4. CLI prints answer.

## Developer-Agent Log

- File: `agent_conversations.md` (stored at repo root).
- This is for the developer-agent collaboration only, not in-app reader users.
- Append one entry per meaningful request/iteration with this pattern:
  - `## Entry <N>`
  - `- Date: <YYYY-MM-DD>`
  - `- Developer Request: <single-line summary>`
  - `- Agent Response Summary: <single-line summary>`
  - `- Files Changed: <comma-separated paths or "none">`

## Testing

- Run all tests:
  - `.venv/bin/python -m pytest -q`
- Relevant tests:
  - `tests/test_cli.py` for reader behavior + `ask` flow
  - `tests/test_providers.py` for HTTP provider payload/header behavior

## Safe Change Rules

- Keep `AIProvider.answer(question, context)` contract stable.
- Preserve viewport-context behavior unless explicitly changing prompt strategy.
- Do not break non-interactive fallback in key reading.
