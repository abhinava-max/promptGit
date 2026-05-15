# PromptGitX

PromptGitX is an AI-powered Git commit assistant built as a Python CLI. It is intended to help generate clean commit messages, review staged changes, and manage LLM provider configuration from the terminal.

## Features

- Interactive CLI built with Typer
- Rich terminal welcome screen
- LLM provider configuration for Groq, OpenAI, Anthropic, Gemini, and Ollama
- AI review reports for commits, commit ranges, pull requests, and staged changes
- LangGraph-based review workflow
- Hunk-based splitting for large file diffs instead of silent trimming
- Verified changed-line references from Git diff hunks
- Terminal, JSON, TXT, DOCX, and PDF report output

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
promptgitx analyze --last --save report.txt
promptgitx analyze --last --save report.json
promptgitx analyze --last --save report.docx
promptgitx analyze --last --save report.pdf
```

If `--save` is not passed, PromptGitX asks whether you want to save the report after displaying it.
Use only one review target per command, such as `--last` or `--staged`, not both.
`--json` prints raw JSON without the welcome banner so it can be used in scripts.

## CLI Option Reference

Global options:

| Long option | Short option | Description |
| --- | --- | --- |
| `--version` | none | Show the installed PromptGitX version and exit. |
| `--help` | none | Show CLI help. |

`promptgitx config` options:

| Long option | Short option | Description |
| --- | --- | --- |
| `--provider` | `-p` | LLM provider to configure: `groq`, `openai`, `anthropic`, `gemini`, or `ollama`. |
| `--models` | `-m` | Comma-separated list of up to five model names. |
| `--api-key` | none | API key for cloud providers. |
| `--base-url` | none | Base URL for local providers like Ollama. |
| `--use` | `-u` | Switch to an already configured provider. |
| `--reset` | `-r` | Reset saved configuration. |

`promptgitx analyze` target options:

| Long option | Short option | Description |
| --- | --- | --- |
| `--commit` | `-c` | Review one specific commit. |
| `--commits` | `-C` | Review multiple commits. Can be provided more than once. |
| `--compare` | `-p` | Review a comparison such as `main..feature-branch`. |
| `--pr` | `-P` | Review a GitHub pull request by number. Requires GitHub CLI. |
| `--last` | `-l` | Review the latest commit. |
| `--last-n` | `-n` | Review the last N commits. |
| `--staged` | `-s` | Review staged changes. |

`promptgitx analyze` output options:

| Long option | Short option | Description |
| --- | --- | --- |
| `--json` | none | Print the raw structured JSON report. |
| `--summary` | none | Print only the short review summary. |
| `--save` | none | Save the report to `.txt`, `.json`, `.docx`, or `.pdf`. |

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

PromptGitX uses the first configured model for the active provider first. During one analyze run, if a model call fails, PromptGitX advances to the next configured model and keeps using that model for later chunks in the same run.

## Analyze Workflow

The `analyze` command uses a LangGraph workflow:

```text
load_diff
  -> parse_diff
  -> split_large_chunks
  -> review_chunks
  -> merge_file_reviews
  -> final_report
```

Workflow details:

- `load_diff` collects the requested Git diff using `git` or `gh`.
- `parse_diff` converts the raw diff into file-level chunks and computes changed-line references from diff hunk headers.
- `split_large_chunks` splits oversized file chunks into hunk-based review chunks without dropping diff data.
- `review_chunks` sends each review chunk to the configured LLM and validates returned references.
- `merge_file_reviews` combines subchunk reviews back into one review per file.
- `final_report` builds the structured report with risk, recommendation, grouped issues, and output-ready data.

Large diffs are split by hunks instead of being cut at an arbitrary character limit. If a single hunk is very large, PromptGitX keeps that hunk intact to avoid corrupting line references.

The final report is mostly built by deterministic Python logic. The LLM reviews individual chunks; Python then normalizes issues, validates references, merges file reviews, calculates risk, and formats the final outputs.

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

This project is in early development. The review report workflow is functional, including saved TXT, JSON, DOCX, and PDF outputs. The chat command is still a placeholder.
