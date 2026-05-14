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
    prompts/             # LangChain prompt templates
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

For package-style local development, install the project in editable mode:

```bash
pip install -e .
```

3. Create your environment file:

```bash
cp .env.example .env
```

## How To Run

Recommended local development command after `pip install -e .`:

```bash
promptgitx
```

View available commands:

```bash
promptgitx --help
```

Show the installed version:

```bash
promptgitx --version
```

You can also run directly from source without installing:

```bash
python3 src/promptgitx/main.py
```

Or run it as a package module:

```bash
PYTHONPATH=src python3 -m promptgitx.main
```

## Commands

Configure an LLM provider interactively:

```bash
promptgitx config
```

Configure a provider with CLI options:

```bash
promptgitx config --provider ollama --models llama3
promptgitx config --provider openai --models gpt-4o-mini --api-key YOUR_API_KEY
```

Reset configuration:

```bash
promptgitx config --reset
```

Start the chat command:

```bash
promptgitx chat
```

Generate a review report:

```bash
promptgitx analyze
```

Analyze examples:

```bash
promptgitx analyze --staged
promptgitx analyze --last
promptgitx analyze --last-n 3
promptgitx analyze --commit COMMIT_HASH
promptgitx analyze --compare main..feature-branch
promptgitx analyze --pr 123
```

Output modes:

```bash
promptgitx analyze --last --summary
promptgitx analyze --last --json
```

## Configuration

PromptGitX supports the following providers:

- Groq
- OpenAI
- Anthropic
- Gemini
- Ollama

The `config` command writes provider settings to a `.env` file, including the current provider, API key or base URL, and up to five model names.

The welcome screen displays the active model as:

```text
Model: <PROVIDER> | <MODEL_NAME>
```

PromptGitX uses the first configured model for the active provider first, then prepares the remaining configured models as fallbacks for later LangGraph/agent workflows.

## Analyze Workflow

The `analyze` command uses a LangGraph workflow:

```text
load_diff -> parse_diff -> review_chunks -> final_report
```

It reuses the existing Git helpers to collect diffs, parses and chunks the diff, reviews each chunk with the configured LLM, then synthesizes a final report. The first configured model is used first; additional configured models are attached as fallbacks.

## Build For Upload

Build source and wheel distributions:

```bash
python3 -m build --sdist --wheel
```

The files will be created in:

```text
dist/
```

## Status

This project is in early development. The CLI structure and provider configuration flow are in place, while the chat and review commands are currently placeholders.
