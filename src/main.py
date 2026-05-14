import typer
from typing import Optional

from ai.llm_providers import set_Config
from misc.heading import clear_screen, show_welcome, console

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
def review():
    """
    Generate a review report for the staged changes.
    """
    console.print("Review report is running")




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
):
    console.print("Configuring PromptGitX")
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
