import typer
from typing import Optional, List

from .config.config import set_Config, reset_config
from .misc.heading import clear_screen, show_welcome
from .misc.console import console
from .misc.analyzer_help import show_analyze_help
from .ai.pr_analyzer import generate_report

app = typer.Typer(
    name="PromptGitX",
    help="AI-powered Git commit assistant.",
    add_completion=False,
)

@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        clear_screen()
        show_welcome()

# ----------------------------------------------------------------
#                    AI-Agent Command
# ----------------------------------------------------------------
@app.command()
def chat():
    """
    Start the AI chat interface to generate Git commit messages.
    """
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
):
    """
    Generate a review report.
    """
    mode = ""
    if commit:
        mode = "commit"
    elif commits:
        mode = "commits"
    elif compare:
        mode = "compare"
    elif pr:
        mode = "pr"
    elif last:
        mode = "last"
    elif last_n:
        mode = "last_n"
    elif staged:
        mode = "staged"
    else:
        show_analyze_help()
        return

    generate_report(mode=mode,
    commit=commit,
    commits=commits,
    compare=compare,
    pr=pr,
    last=last,
    last_n=last_n,
    staged=staged,
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
    if reset:
        console.print("Resetting configurations")
        reset_config()
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
    clear_screen()
    show_welcome()
    app()

if __name__ == "__main__":
    main()
