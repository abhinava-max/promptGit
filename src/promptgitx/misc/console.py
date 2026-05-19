from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme
import sys

promptgitx_theme = Theme({
    "markdown.h1": "bold #c084fc",
    "markdown.h2": "bold #38bdf8",
    "markdown.h3": "bold #818cf8",
    "markdown.strong": "bold #f8fafc",
    "markdown.em": "italic #94a3b8",
    "markdown.code": "bold #22c55e",
    "markdown.code_block": "#e2e8f0 on #111827",
    "markdown.block_quote": "#94a3b8 italic",
    "markdown.item": "#e2e8f0",
    "markdown.hr": "#475569",
    "markdown.table": "#e2e8f0",
    "markdown.table.header": "bold #38bdf8",
    "repr.str": "#22c55e",
})

# Detect if output is a TTY (interactive terminal)
if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
    console = Console(color_system="truecolor", theme=promptgitx_theme)
else:
    console = Console(color_system=None, theme=promptgitx_theme)

def print_chat_response(response: str) -> None:
    try:
        console.print(
            Panel(
                Markdown(response, code_theme="github-dark"),
                title="[bold #38bdf8]PromptGitX[/bold #38bdf8]",
                border_style="#818cf8",
                padding=(1, 2),
            )
        )
    except Exception:
        console.print(response)
