from langchain_core.output_parsers import StrOutputParser
from typer.testing import CliRunner

from promptgitx.ai.llm_provider import RuntimeModelRouter
from promptgitx.misc.console import console
from promptgitx.prompts import get_chat_help_prompt


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
    help_context = collect_promptgitx_help(app)

    while True:
        user_input = console.input("\n[bold yellow]PromptGitX>[/bold yellow] ")
        if user_input.strip().lower() in ["exit", "quit", ":q"]:
            break

        response = ask_help_agent(user_input, help_context)
        console.print(f"\n[bold green]AI[/bold green] > {response}")


def ask_help_agent(user_input: str, help_context: str) -> str:
    prompt = get_chat_help_prompt()
    model_router = RuntimeModelRouter()
    chain = prompt | model_router.create_current_chat_model() | StrOutputParser()
    return chain.invoke(
        {
            "help_context": help_context,
            "user_input": user_input,
        }
    )
