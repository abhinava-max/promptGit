import subprocess
from typing import List


def run_command(command: List[str], cwd: str | None = None) -> str:
    """
    Runs a terminal command safely and returns stdout.

    Args:
        command: Command as a list, example: ["git", "status"]
        cwd: Optional working directory

    Returns:
        Command output as string

    Raises:
        RuntimeError: If command fails
    """

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed: {' '.join(command)}\n\nError:\n{result.stderr.strip()}"
            )

        return result.stdout.strip()

    except FileNotFoundError:
        raise RuntimeError(
            f"Command not found: {command[0]}. Please make sure it is installed."
        )


def command_exists(command: str) -> bool:
    """
    Checks if a command exists in the system.
    Example: git, gh
    """

    try:
        subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        return True

    except FileNotFoundError:
        return False