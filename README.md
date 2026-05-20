# PromptGitX

PromptGitX is an AI-powered Git review assistant packaged as a Python CLI. It helps you inspect commits, staged changes, branches, and pull requests from the terminal, then produces structured review reports in terminal, JSON, TXT, DOCX, or PDF formats.

## Highlights

- Review staged changes, commits, commit ranges, pull requests, and recent history.
- Generate structured AI review reports with risk, recommendation, grouped issues, and changed-line references.
- Save reports as `.txt`, `.json`, `.docx`, or `.pdf`.
- Configure Groq, OpenAI, Anthropic, Gemini, or local Ollama models from the CLI.
- Use up to five fallback models per provider during one review run.
- Ask PromptGitX usage questions and generate review reports through the scoped `chat` command.
- Run as a normal Python package with a `promptgitx` console command.

## Installation

Install from PyPI:

```bash
python3 -m pip install promptgitx
```

Check the installed version:

```bash
promptgitx --version
```

View available commands:

```bash
promptgitx --help
```

## Quick Start

Configure an LLM provider:

```bash
promptgitx config
```

Review staged changes:

```bash
promptgitx analyze --staged
```

Review the latest commit:

```bash
promptgitx analyze --last
```

Save a PDF report:

```bash
promptgitx analyze --last --save review.pdf
```

Save to a specific path:

```bash
promptgitx analyze --staged --save ./reports/staged-review.pdf
```

## Commands

### `promptgitx config`

Configure the LLM provider used by PromptGitX.

Interactive setup:

```bash
promptgitx config
```

Configure directly with options:

```bash
promptgitx config --provider groq --models MODEL_NAME --api-key YOUR_API_KEY
promptgitx config --provider openai --models MODEL_NAME --api-key YOUR_API_KEY
promptgitx config --provider anthropic --models MODEL_NAME --api-key YOUR_API_KEY
promptgitx config --provider gemini --models MODEL_NAME --api-key YOUR_API_KEY
promptgitx config --provider ollama --models MODEL_NAME --base-url http://localhost:11434
```

Switch to an already configured provider:

```bash
promptgitx config --use groq
```

Reset saved PromptGitX configuration:

```bash
promptgitx config --reset
```

### `promptgitx analyze`

Generate an AI review report for one Git target.

Examples:

```bash
promptgitx analyze --staged
promptgitx analyze --last
promptgitx analyze --last-n 3
promptgitx analyze --commit COMMIT_HASH
promptgitx analyze --compare main..feature-branch
promptgitx analyze --pr 123
```

Use only one review target at a time. For example, use `--staged` or `--last`, not both.

Output examples:

```bash
promptgitx analyze --last --summary
promptgitx analyze --last --json
promptgitx analyze --last --save report.txt
promptgitx analyze --last --save report.json
promptgitx analyze --last --save report.docx
promptgitx analyze --last --save report.pdf
```

If `--save` is not passed, PromptGitX displays the report and then asks whether you want to save it.

### `promptgitx chat`

Start a scoped PromptGitX chat:

```bash
promptgitx chat
```

The chat command answers questions about PromptGitX CLI usage and can generate review reports conversationally. If a report request is missing details, PromptGitX asks a follow-up question and remembers the pending report request.

Examples:

```text
PromptGitX> make me a PR report
PromptGitX> 2
```

```text
PromptGitX> review my staged changes
PromptGitX> create a report for the last 3 commits
PromptGitX> compare main..feature-branch
```

Chat report generation preserves the same terminal report styling as `promptgitx analyze`. It does not execute repository-changing Git operations such as push, commit, checkout, merge, or rebase.

## CLI Reference

Global options:

| Option | Description |
| --- | --- |
| `--version` | Show the installed PromptGitX version and exit. |
| `--help` | Show CLI help. |

`promptgitx config` options:

| Option | Short | Description |
| --- | --- | --- |
| `--provider` | `-p` | Provider to configure: `groq`, `openai`, `anthropic`, `gemini`, or `ollama`. |
| `--models` | `-m` | Comma-separated list of up to five model names. |
| `--api-key` | none | API key for cloud providers. |
| `--base-url` | none | Base URL for local providers like Ollama. |
| `--use` | `-u` | Switch to an already configured provider. |
| `--reset` | `-r` | Remove saved PromptGitX configuration. |

`promptgitx analyze` target options:

| Option | Short | Description |
| --- | --- | --- |
| `--commit` | `-c` | Review one commit by SHA, tag, or revision. |
| `--commits` | `-C` | Review multiple commits. Can be provided more than once. |
| `--compare` | `-p` | Review a range such as `main..feature-branch`. |
| `--pr` | `-P` | Review a GitHub pull request by number. Requires the GitHub CLI. |
| `--last` | `-l` | Review the latest commit. |
| `--last-n` | `-n` | Review the last N commits. |
| `--staged` | `-s` | Review currently staged changes. |

`promptgitx analyze` output options:

| Option | Description |
| --- | --- |
| `--json` | Print the raw structured JSON report. |
| `--summary` | Print only the short summary and final recommendation. |
| `--save` | Save the report to `.txt`, `.json`, `.docx`, or `.pdf`. |

## Configuration

PromptGitX stores its provider settings at:

```text
~/.promptgitx/.env
```

This keeps your API keys in one user-level location instead of creating `.env` files in whichever project directory you run the CLI from.

To use a different config file intentionally, set `PROMPTGITX_ENV_PATH`:

```bash
PROMPTGITX_ENV_PATH=/path/to/promptgitx.env promptgitx analyze --last
```

The config file stores values such as:

```text
CURRENT_PROVIDER=GROQ
GROQ_API_KEY=...
GROQ_MODEL_1=MODEL_NAME
```

The active model appears in the welcome screen as:

```text
Model: <PROVIDER> | <MODEL_NAME>
```

## Model Fallbacks

Each provider can store up to five model names. PromptGitX starts with model 1. If a model call fails during a review run, PromptGitX advances to the next configured model and continues the run with that fallback.

Example:

```bash
promptgitx config --provider groq --models MODEL_1,MODEL_2
```

## Report Formats

PromptGitX can print or save reports in these formats:

| Format | Usage |
| --- | --- |
| Terminal | Default formatted report in the terminal. |
| JSON | `--json` or `--save report.json`. Useful for scripts. |
| TXT | `--save report.txt`. Plain text report. |
| DOCX | `--save report.docx`. Word-compatible document. |
| PDF | `--save report.pdf`. Styled PDF report. |

When saving to a path, PromptGitX creates missing parent folders when possible:

```bash
promptgitx analyze --last --save ./reports/latest-review.pdf
```

## How Analysis Works

The `analyze` command uses a LangGraph workflow:

```text
load_diff
  -> parse_diff
  -> split_large_chunks
  -> review_chunks
  -> merge_file_reviews
  -> final_report
```

What happens internally:

- `load_diff` collects the requested Git diff using `git` or `gh`.
- `parse_diff` turns raw diffs into file-level chunks and changed-line references.
- `split_large_chunks` splits oversized diffs by hunks instead of silently trimming content.
- `review_chunks` sends review chunks to the configured LLM.
- `merge_file_reviews` combines chunk-level findings back into file-level findings.
- `final_report` builds the final structured report and output data.

PromptGitX keeps large hunks intact where possible so line references do not get corrupted by arbitrary slicing.

## Chat Report Flow

The `chat` command uses a LangGraph chat workflow:

```text
classify_chat_intent
  -> promptgitx_query
  -> promptgitx_report_generation
  -> git_github_question
  -> git_workflow_execution
```

For report generation, chat extracts the report target with an LLM-backed structured request parser. It supports natural follow-ups such as:

```text
PromptGitX> make me a report
PromptGitX> staged changes
```

or:

```text
PromptGitX> make me a PR report
PromptGitX> second pr
```

Repository-changing Git/GitHub requests are routed separately from report generation.

## Requirements

- Python 3.10 or newer.
- Git installed and available on `PATH`.
- GitHub CLI `gh` for `promptgitx analyze --pr`.
- An API key for a cloud LLM provider, or a running Ollama server for local models.

## Local Development

Clone the repository:

```bash
git clone https://github.com/abhinava-max/promptGit.git
cd promptGit
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install in editable mode:

```bash
python3 -m pip install -e .
```

Run from the installed console command:

```bash
promptgitx --help
```

Run directly from source:

```bash
python3 src/promptgitx/main.py --help
```

Build package distributions:

```bash
python3 -m build
```

Check distributions before publishing:

```bash
python3 -m twine check dist/*
```

## Project Links

- Source: https://github.com/abhinava-max/promptGit
- Issues: https://github.com/abhinava-max/promptGit/issues
- PyPI: https://pypi.org/project/promptgitx/

## Status

PromptGitX is in early development. The review workflow and report exporters are functional, and the CLI surface may still evolve between minor versions.

## License

MIT
