"""State definitions for PromptGitX LangGraph workflows."""

from typing import Any, TypedDict


class ReviewGraphState(TypedDict, total=False):
    mode: str
    commit: str | None
    commits: list[str] | None
    compare: str | None
    pr: int | None
    last: bool | None
    last_n: int | None
    staged: bool | None
    repo_context: str
    diff: str
    diff_summary: dict[str, Any]
    chunks: list[dict[str, Any]]
    chunk_reviews: list[str]
    final_report: str
    model_name: str
