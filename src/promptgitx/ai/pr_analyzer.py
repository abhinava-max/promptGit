from typing import Optional, List
from ..misc.console import console
from ..reports import render_summary_report, render_terminal_report, save_report

from .json_utils import to_pretty_json
from .review_graph import run_review_graph


def generate_report(
    mode: str,
    commit: Optional[str] = None,
    commits: Optional[List[str]] = None,
    compare: Optional[str] = None,
    pr: Optional[int] = None,
    last: Optional[bool] = None,
    last_n: Optional[int] = None,
    staged: Optional[bool] = None,
    output_json: bool = False,
    summary_only: bool = False,
    save_path: Optional[str] = None,
):
    """
    Generate a review report.
    """
    try:
        result = run_review_graph(
            {
                "mode": mode,
                "commit": commit,
                "commits": commits,
                "compare": compare,
                "pr": pr,
                "last": last,
                "last_n": last_n,
                "staged": staged,
            }
        )
        report = result.get("report")

        if not report:
            console.print("No report was generated.")
            return

        if output_json:
            console.print(to_pretty_json(report))
        elif summary_only:
            console.print(render_summary_report(report))
        else:
            console.print(render_terminal_report(report))

        if save_path:
            saved_path = save_report(report, save_path)
            console.print(f"\nReport saved to: {saved_path}", style="bold #22c55e")
        elif not output_json and not summary_only:
            maybe_prompt_save(report)

    except Exception as error:
        console.print(f"Failed to generate review report: {error}", style="bold #fb7185")


def maybe_prompt_save(report: dict):
    answer = console.input("\nSave this report? [y/N]: ").strip().lower()

    if answer not in {"y", "yes"}:
        return

    report_format = console.input("Format (json, txt, docx, pdf): ").strip().lower()

    if report_format not in {"txt", "json", "docx", "pdf"}:
        console.print("Invalid format. Use json, txt, docx, or pdf.", style="bold #fb7185")
        return

    try:
        saved_path = save_report(report, report_format=report_format)
        console.print(f"Report saved to: {saved_path}", style="bold #22c55e")
    except ValueError as error:
        console.print(str(error), style="bold #fb7185")
