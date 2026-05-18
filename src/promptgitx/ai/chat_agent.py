from typer.testing import CliRunner
from .chat_graph import run_chat_graph

from promptgitx.misc.console import console


HELP_COMMANDS = [
    [],
    ["analyze"],
    ["config"],
    ["chat"],
]


def collect_promptgitx_help(app) -> str:
    runner = CliRunner()
    sections = []

    for command in HELP_COMMANDS:
        title = "promptgitx"

        if command:
            title = f"{title} {' '.join(command)}"

        result = runner.invoke(app, [*command, "--help"], terminal_width=120)
        output = result.output.strip()

        if not output:
            output = f"Help unavailable for {title}."

        sections.append(f"## {title} --help\n{output}")

    return "\n\n".join(sections)


def run_help_chat(app) -> None:
    while True:
        user_input = console.input("\n[bold yellow]PromptGitX>[/bold yellow] ")
        if user_input.strip().lower() in ["exit", "quit", ":q"]:
            break

        result = run_chat_graph(
            {
                "user_input": user_input,
                "promptgitx_app": app,
            }
        )
        console.print(result.get("response", "No response generated."))
