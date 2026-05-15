"""Save PromptGitX reports to local files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from ..ai.json_utils import to_pretty_json
from .docx_writer import create_docx_report
from .formatter import format_terminal_report
from .pdf_writer import create_pdf_report


SUPPORTED_FORMATS = {"txt", "json", "docx", "pdf"}


def default_report_path(report_format: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path(f"promptgitx-report-{timestamp}.{report_format}")


def infer_report_format(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")

    if suffix in SUPPORTED_FORMATS:
        return suffix

    raise ValueError("Only .txt, .json, .docx, and .pdf report formats are supported for now.")


def save_report(
    report: dict[str, Any],
    path: str | Path | None = None,
    report_format: str | None = None,
) -> Path:
    if report_format:
        report_format = report_format.lower().strip()

        if report_format not in SUPPORTED_FORMATS:
            raise ValueError("Only txt, json, docx, and pdf report formats are supported for now.")

    if path is None:
        if report_format is None:
            report_format = "txt"

        output_path = default_report_path(report_format)
    else:
        output_path = Path(path)

        if report_format is None:
            report_format = infer_report_format(output_path)

        if not output_path.suffix:
            output_path = output_path.with_suffix(f".{report_format}")

    if report_format == "docx":
        create_docx_report(report, output_path)
        return output_path

    if report_format == "pdf":
        create_pdf_report(report, output_path)
        return output_path

    if report_format == "json":
        content = to_pretty_json(report)
    else:
        content = format_terminal_report(report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")

    return output_path
