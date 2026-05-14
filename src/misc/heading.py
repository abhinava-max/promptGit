from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from pyfiglet import Figlet
from misc.console import console
import os
import sys



def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )


def interpolate_color(color1, color2, ratio: float):
    r = int(color1[0] + (color2[0] - color1[0]) * ratio)
    g = int(color1[1] + (color2[1] - color1[1]) * ratio)
    b = int(color1[2] + (color2[2] - color1[2]) * ratio)
    return r, g, b


def get_gradient_text(text: str) -> Text:
    figlet = Figlet(font="big")
    big_text = figlet.renderText(text)

    # Blue → Purple → Pink
    colors = [
    "#f97316",
    "#fb7185",
    "#c084fc",
    "#818cf8",
    ]

    rgb_colors = [hex_to_rgb(color) for color in colors]

    t = Text()
    length = max(len(big_text) - 1, 1)

    for i, char in enumerate(big_text):
        ratio = i / length

        # Decide between which two colors the current character is
        segment_count = len(rgb_colors) - 1
        segment = min(int(ratio * segment_count), segment_count - 1)

        segment_start = segment / segment_count
        segment_end = (segment + 1) / segment_count
        segment_ratio = (ratio - segment_start) / (segment_end - segment_start)

        r, g, b = interpolate_color(
            rgb_colors[segment],
            rgb_colors[segment + 1],
            segment_ratio,
        )

        t.append(char, style=f"bold rgb({r},{g},{b})")

    return t

def show_welcome():
    heading = get_gradient_text("PromptGitX")

    subtitle = Text("AI-powered Git commit assistant", style="bold #a78bfa")
    description = Text(
        "Generate clean, meaningful, and professional Git commit messages.",
        style="#94a3b8",
    )

    help_text = Text()
    help_text.append("Run ", style="#64748b")
    help_text.append("promptgitx --help", style="bold cyan")
    help_text.append(" to view available commands.", style="#64748b")

    content = Text()
    content.append("\n")
    content.append(subtitle)
    content.append("\n")
    content.append(description)
    content.append("\n\n")
    content.append(help_text)

    console.print()
    console.print(Align.center(heading))
    console.print(
        Panel(
            Align.center(content),
            border_style="#6366f1",
            padding=(1, 4),
            title="[bold #c084fc]Welcome[/bold #c084fc] | [bold #c084fc]PromptGitX CLI[/bold #c084fc]",
        )
    )
    console.print()

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")
    sys.stdout.write("\033[3J")
    sys.stdout.flush()