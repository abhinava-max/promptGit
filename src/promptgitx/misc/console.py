from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import sys

# Detect if output is a TTY (interactive terminal)
if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
    console = Console(color_system="truecolor")
else:
    console = Console(color_system=None)

def print_chat_response(response: str) -> None:
    try:
        console.print(Panel(Markdown(response), 
                        title="[bold #c084fc]PromptGitX[/bold #c084fc]",
                        border_style="#818cf8",
                        padding=(1, 2)))
    except Exception as e:
        console.print(response)
    