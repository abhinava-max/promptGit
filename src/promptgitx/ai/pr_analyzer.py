from typing import Optional, List
from ..misc.console import console
from ..reports import format_summary_report, format_terminal_report

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
            console.print(format_summary_report(report))
        else:
            console.print(format_terminal_report(report))

    except Exception as error:
        console.print(f"Failed to generate review report: {error}", style="bold #fb7185")
