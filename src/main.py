import typer
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
def config():
    """
    Configure PromptGitX.
    """
    console.print("Configuring PromptGitX")



# ----------------------------------------------------------------
#                    Main Function
# ----------------------------------------------------------------
def main():
    clear_screen()
    show_welcome()
    app()

if __name__ == "__main__":
    main()