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
    review_chunks: list[dict[str, Any]]
    chunk_reviews: list[dict[str, Any]]
    file_reviews: list[dict[str, Any]]
    report: dict[str, Any]
    final_report: str
    model_name: str

class ChatGraphState(TypedDict, total=False):
    user_input: str
    help_context: str
    promptgitx_app: Any
    intent: str
    intent_reason: str
    response: str
    refusal_reason: str
    pending_report_request: dict[str, Any] | None
    report_request: dict[str, Any]
    response_type: str
    report: dict[str, Any]
