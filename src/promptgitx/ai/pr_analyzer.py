from typing import Optional, List
from ..misc.console import console

from ..gitcodes.diff_fetcher import (
    get_commit_diff,
    get_multiple_commits_diff,
    get_last_commit_diff,
    get_last_n_commits_diff,
    get_staged_diff,
    get_compare_diff,
    get_pr_diff,
)


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
    match mode:
        case "commit":
            diff = get_commit_diff(commit)
            console.print(diff)
        case "commits":
            diff = get_multiple_commits_diff(commits)
            console.print(diff)
        case "compare":
            diff = get_compare_diff(compare)
            console.print(diff)
        case "pr":
            diff = get_pr_diff(pr)
            console.print(diff)
        case "last":
            diff = get_last_commit_diff()
            console.print(diff)
        case "last_n":
            diff = get_last_n_commits_diff(last_n)
            console.print(diff)
        case "staged":
            diff = get_staged_diff()
            console.print(diff)
