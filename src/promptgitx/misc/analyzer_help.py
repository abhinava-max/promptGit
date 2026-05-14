import os
import sys
import shutil
import subprocess
from pathlib import Path


def show_analyze_help():
    # Check which pip command exists
    pip_cmd = shutil.which("pip") or shutil.which("pip3")

    # Check if promptgitx package is installed
    is_installed = False

    if pip_cmd:
        result = subprocess.run(
            [pip_cmd, "show", "promptgitx"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        is_installed = result.returncode == 0

    # If installed globally / in venv, use CLI command
    if is_installed and shutil.which("promptgitx"):
        subprocess.run(["promptgitx", "analyze", "--help"])
    else:
        # Otherwise run from local source
        python_cmd = sys.executable
        src_path = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(src_path)
        subprocess.run(
            [python_cmd, "-m", "promptgitx.main", "analyze", "--help"],
            env=env,
        )

    return
