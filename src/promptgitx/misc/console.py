from rich.console import Console
import sys

# Detect if output is a TTY (interactive terminal)
if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
    console = Console(color_system="truecolor")
else:
    console = Console(color_system=None)
    