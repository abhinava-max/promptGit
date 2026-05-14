from typing import Optional, List
from ..misc.console import console

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
        console.print(result.get("final_report", "No report was generated."))

    except Exception as error:
        console.print(f"Failed to generate review report: {error}", style="bold #fb7185")
