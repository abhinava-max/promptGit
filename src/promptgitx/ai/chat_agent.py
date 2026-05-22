from typer.testing import CliRunner
from .chat_graph import run_chat_graph
from promptgitx.misc.console import console, print_chat_response
from promptgitx.reports import render_terminal_report
from promptgitx.ai.pr_analyzer import maybe_prompt_save


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
    pending_report_request = None
    pending_git_workflow_request = None

    while True:
        user_input = console.input("\n[bold #38bdf8]PromptGitX>[/bold #38bdf8] ")

        if user_input.strip().lower() in ["exit", "quit", ":q"]:
            break
        console.print("")

        # Printing Status Text
        status_text = "[bold #38bdf8]PromptGitX is thinking...[/bold #38bdf8]"
        
        with console.status(status_text):
            result = run_chat_graph(
            {
            "user_input": user_input,
            "promptgitx_app": app,
            "pending_report_request": pending_report_request,
            "pending_git_workflow_request": pending_git_workflow_request,
            }
        )
        pending_report_request = result.get("pending_report_request")
        pending_git_workflow_request = result.get("pending_git_workflow_request")

        if result.get("response_type") == "report":
            report = result.get("report")
            console.print(render_terminal_report(result["report"]))
            maybe_prompt_save(report)
        else:
            print_chat_response(result.get("response", "No response generated."))
