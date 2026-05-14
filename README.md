# PromptGitX

PromptGitX is an AI-powered Git commit assistant built as a Python CLI. It is intended to help generate clean commit messages, review staged changes, and manage LLM provider configuration from the terminal.

## Features

- Interactive CLI built with Typer
- Rich terminal welcome screen
- LLM provider configuration for Groq, OpenAI, Anthropic, Gemini, and Ollama
- Placeholder commands for chat-based commit message generation and review reports

## Project Structure

```text
pyproject.toml          # PyPI/build metadata
src/
  promptgitx/
    main.py              # CLI entry point
    ai/                  # AI review/report helpers
    config/              # LLM provider configuration helpers
    gitcodes/            # Git diff and repository helpers
    misc/                # Rich/figlet terminal UI helpers
```

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

For package-style local development:

```bash
pip install -e .
```

3. Create your environment file:

```bash
cp src/.env.example .env
```

## Usage

Run the CLI after installing locally:

```bash
promptgitx
```

View available commands:

```bash
promptgitx --help
```

Configure an LLM provider:

```bash
promptgitx config
```

Start the chat command:

```bash
promptgitx chat
```

Generate a review report:

```bash
promptgitx analyze
```

## Configuration

PromptGitX supports the following providers:

- Groq
- OpenAI
- Anthropic
- Gemini
- Ollama

The `config` command writes provider settings to a `.env` file, including the current provider, API key or base URL, and up to five model names.

## Status

This project is in early development. The CLI structure and provider configuration flow are in place, while the chat and review commands are currently placeholders.
