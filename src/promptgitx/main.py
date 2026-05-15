import typer
from typing import Optional, List
from pathlib import Path
import sys


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from promptgitx.config.config import set_Config, reset_config, switch_provider
    from promptgitx.misc.heading import clear_screen, show_welcome
    from promptgitx.misc.console import console
    from promptgitx.misc.analyzer_help import show_analyze_help
    from promptgitx import __version__
else:
    from .config.config import set_Config, reset_config, switch_provider
    from .misc.heading import clear_screen, show_welcome
    from .misc.console import console
    from .misc.analyzer_help import show_analyze_help
    from . import __version__

app = typer.Typer(
    name="PromptGitX",
    help="AI-powered Git commit assistant.",
    add_completion=False,
)

def print_version(value: bool):
    if value:
        console.print(f"PromptGitX {__version__}")
        raise typer.Exit()


def show_app_header():
    from promptgitx.ai.llm_provider import get_current_model_display

    clear_screen()
    show_welcome(model_name=get_current_model_display())


def should_show_loading_message() -> bool:
    quiet_options = {"--json", "--version", "--help", "-h"}
    return not any(option in quiet_options for option in sys.argv[1:])


def get_analyze_mode(
    commit: Optional[str],
    commits: Optional[List[str]],
    compare: Optional[str],
    pr: Optional[int],
    last: Optional[bool],
    last_n: Optional[int],
    staged: Optional[bool],
) -> str | None:
    selected_modes = []

    if commit:
        selected_modes.append("commit")
    if commits:
        selected_modes.append("commits")
    if compare:
        selected_modes.append("compare")
    if pr:
        selected_modes.append("pr")
    if last:
        selected_modes.append("last")
    if last_n:
        selected_modes.append("last_n")
    if staged:
        selected_modes.append("staged")

    if len(selected_modes) > 1:
        raise typer.BadParameter(
            "Use only one review target at a time: --commit, --commits, "
            "--compare, --pr, --last, --last-n, or --staged."
        )

    if not selected_modes:
        return None

    return selected_modes[0]


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=print_version,
        is_eager=True,
        help="Show the PromptGitX version and exit.",
    ),
):
    if ctx.invoked_subcommand is None:
        show_app_header()

# ----------------------------------------------------------------
#                    AI-Agent Command
# ----------------------------------------------------------------
@app.command()
def chat():
    """
    Start the AI chat interface to generate Git commit messages.
    """
    show_app_header()
    console.print("Chat is running")



# ----------------------------------------------------------------
#                   Review Report Command
# ----------------------------------------------------------------
@app.command()
def analyze(
    commit: Optional[str] = typer.Option(
        None,
        "--commit",
        "-c",
        help="Generate a review report for any Specific Commit.",
    ),
    commits: Optional[List[str]] = typer.Option(
        None,
        "--commits",
        "-C",
        help="Generate a review report for Multiple Commits.",
    ),
    compare: Optional[str] = typer.Option(
        None,
        "--compare",
        "-p",
        help="Generate a review report by comparing multiple branches/tags/commits",
    ),
    pr: Optional[int] = typer.Option(
        None,
        "--pr",
        "-P",
        help="Generate a review report for a Pull Request.",
    ),
    last: Optional[bool] = typer.Option(
        None,
        "--last",
        "-l",
        help="Generate a review report for the last Commit.",
    ),
    last_n: Optional[int] = typer.Option(
        None,
        "--last-n",
        "-n",
        help="Generate a review report for the last n Commits.",
    ),
    staged: Optional[bool] = typer.Option(
        None,
        "--staged",
        "-s",
        help="Generate a review report for the Staged Changes.",
    ),
    output_json: Optional[bool] = typer.Option(
        None,
        "--json",
        help="Print the raw structured JSON report.",
    ),
    summary: Optional[bool] = typer.Option(
        None,
        "--summary",
        help="Print only the short review summary.",
    ),
    save: Optional[str] = typer.Option(
        None,
        "--save",
        help="Save the report to a .json, .txt, .docx, or .pdf file.",
    ),
):
    """
    Generate a review report.
    """
    if output_json and summary:
        raise typer.BadParameter("Use either --json or --summary, not both.")

    mode = get_analyze_mode(
        commit=commit,
        commits=commits,
        compare=compare,
        pr=pr,
        last=last,
        last_n=last_n,
        staged=staged,
    )

    if mode is None:
        show_app_header()
        show_analyze_help()
        return

    if not output_json:
        show_app_header()

    from promptgitx.ai.pr_analyzer import generate_report

    generate_report(
        mode=mode,
        commit=commit,
        commits=commits,
        compare=compare,
        pr=pr,
        last=last,
        last_n=last_n,
        staged=staged,
        output_json=bool(output_json),
        summary_only=bool(summary),
        save_path=save,
    )




# ----------------------------------------------------------------
#                      Config Command
# ----------------------------------------------------------------
@app.command()
def config(
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider to configure: groq, openai, anthropic, gemini, ollama.",
    ),
    models: Optional[str] = typer.Option(
        None,
        "--models",
        "-m",
        help="Comma-separated list of up to 5 model names.",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="API key for cloud providers.",
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        help="Base URL for local providers like Ollama.",
    ),
    use: Optional[str] = typer.Option(
        None,
        "--use",
        "-u",
        help="Switch to an already configured provider.",
    ),
    reset: Optional[bool] = typer.Option(
        None,
        "--reset",
        "-r",
        help="Reset configurations.",
    ),
):
    """
    Configure PromptGitX
    """
    show_app_header()

    if reset:
        console.print("Resetting configurations")
        reset_config()
        return
    if use:
        switch_provider(use)
        return
    else:
        set_Config(
            provider=provider,
            models=models,
            api_key=api_key,
            base_url=base_url,
        )



# ----------------------------------------------------------------
#                    Main Function
# ----------------------------------------------------------------
def main():
    if should_show_loading_message():
        console.print("[yellow]Please wait, PromptGitX is loading...[/yellow]")

    app()

if __name__ == "__main__":
    main()