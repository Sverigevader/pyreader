# pyreader

A lightweight terminal EPUB reader in Python, designed so an LLM can be integrated later as a text tool.

## Features

- Read `.epub` files (metadata + linear reading order)
- List chapters
- Read chapter text in terminal
- Search text in loaded chapters
- Pluggable AI provider interface (`AIProvider`)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pyreader path/to/book.epub
```

Use OpenAI provider:

```bash
export OPENAI_API_KEY=your_key
pyreader path/to/book.epub --ai-provider openai --ai-model gpt-4o-mini
```

Once launched, run `help` for commands.

## Example commands

- `meta`
- `chapters`
- `read 1`
- `next`
- `prev`
- `search whales`
- `ask What happened in this scene?`

## LLM integration

The app includes an interface at `src/pyreader/ai.py`:

- `AIProvider` protocol
- `NoopProvider` default implementation

To integrate another model, add a new provider class implementing `answer(question, context)` and wire it in `src/pyreader/cli.py`.

`ask` currently sends only the currently visible text window from the reader, not the full chapter.
