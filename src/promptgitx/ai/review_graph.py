"""LangGraph workflow for reviewing Git diffs."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph

from .graph_state import ReviewGraphState
from .json_utils import extract_json_object, to_pretty_json
from .llm_provider import create_chat_model_with_fallbacks, get_current_model_display
from .report_builder import build_report, normalize_file_review
from ..gitcodes.diff_fetcher import (
    get_commit_diff,
    get_compare_diff,
    get_last_commit_diff,
    get_last_n_commits_diff,
    get_multiple_commits_diff,
    get_pr_diff,
    get_staged_diff,
)
from ..gitcodes.diff_parser import (
    chunk_diff_by_file,
    filter_large_diff_chunks,
    summarize_diff,
)
from ..gitcodes.git_info import get_current_branch, get_repo_root
from ..prompts import get_chunk_review_prompt


MAX_CHUNK_CHARS = 12000
MAX_NUMBERED_CHANGED_LINES = 120


def format_numbered_changed_lines(chunk: dict) -> str:
    changed_lines = chunk.get("changed_lines", [])

    if not changed_lines:
        return "No exact changed line references were parsed. Use changed block."

    lines = []

    for item in changed_lines[:MAX_NUMBERED_CHANGED_LINES]:
        prefix = "+" if item.get("kind") == "added" else "-"
        lines.append(f"{item.get('reference')}: {prefix} {item.get('content', '')}")

    remaining = len(changed_lines) - len(lines)

    if remaining > 0:
        lines.append(f"... {remaining} more changed line(s) omitted. Use changed block for omitted lines.")

    return "\n".join(lines)


def get_repo_context() -> str:
    context_parts = []

    try:
        context_parts.append(f"Root: {get_repo_root()}")
    except RuntimeError:
        pass

    try:
        context_parts.append(f"Branch: {get_current_branch()}")
    except RuntimeError:
        pass

    if not context_parts:
        return "Repository context unavailable."

    return "\n".join(context_parts)


def load_diff_node(state: ReviewGraphState) -> ReviewGraphState:
    mode = state["mode"]

    match mode:
        case "commit":
            diff = get_commit_diff(state.get("commit"))
        case "commits":
            diff = get_multiple_commits_diff(state.get("commits") or [])
        case "compare":
            diff = get_compare_diff(state.get("compare"))
        case "pr":
            diff = get_pr_diff(state.get("pr") or 0)
        case "last":
            diff = get_last_commit_diff()
        case "last_n":
            diff = get_last_n_commits_diff(state.get("last_n") or 0)
        case "staged":
            diff = get_staged_diff()
        case _:
            raise ValueError(f"Unsupported analyze mode: {mode}")

    return {
        "diff": diff,
        "repo_context": get_repo_context(),
        "model_name": get_current_model_display(),
    }


def parse_diff_node(state: ReviewGraphState) -> ReviewGraphState:
    diff = state.get("diff", "")
    summary = summarize_diff(diff)
    chunks = filter_large_diff_chunks(
        chunk_diff_by_file(diff),
        max_chars=MAX_CHUNK_CHARS,
    )

    return {
        "diff_summary": summary,
        "chunks": chunks,
    }


def review_chunks_node(state: ReviewGraphState) -> ReviewGraphState:
    chunks = state.get("chunks", [])

    if not chunks:
        return {
            "chunk_reviews": [],
            "file_reviews": [],
        }

    chain = get_chunk_review_prompt() | create_chat_model_with_fallbacks() | StrOutputParser()
    chunk_reviews = []
    file_reviews = []

    for index, chunk in enumerate(chunks, start=1):
        try:
            raw_review = chain.invoke(
                {
                    "mode": state["mode"],
                    "repo_context": state.get("repo_context", ""),
                    "file_path": chunk.get("file_path", "unknown"),
                    "added_lines_count": chunk.get("added_lines_count", 0),
                    "removed_lines_count": chunk.get("removed_lines_count", 0),
                    "numbered_changed_lines": format_numbered_changed_lines(chunk),
                    "raw_diff": chunk.get("raw_diff", ""),
                }
            )
            parsed_review = extract_json_object(raw_review)
            file_review = normalize_file_review(parsed_review, chunk)
        except Exception as error:
            file_review = normalize_file_review(
                {
                    "file_path": chunk.get("file_path", "unknown"),
                    "summary": "Model output could not be parsed as valid JSON.",
                    "issues": [
                        {
                            "category": "maintainability",
                            "severity": "medium",
                            "line_reference": "file review",
                            "message": f"AI review for this file failed JSON parsing: {error}",
                            "suggestion": "Run the review again or inspect this file manually.",
                        }
                    ],
                },
                chunk,
            )

        file_reviews.append(file_review)
        chunk_reviews.append(
            {
                "chunk": index,
                "file_path": file_review["file_path"],
                "review": file_review,
            }
        )

    return {
        "chunk_reviews": chunk_reviews,
        "file_reviews": file_reviews,
    }


def final_report_node(state: ReviewGraphState) -> ReviewGraphState:
    report = build_report(
        state=state,
        file_reviews=state.get("file_reviews", []),
    )

    return {
        "report": report,
        "final_report": to_pretty_json(report),
    }


def create_review_graph():
    graph = StateGraph(ReviewGraphState)
    graph.add_node("load_diff", load_diff_node)
    graph.add_node("parse_diff", parse_diff_node)
    graph.add_node("review_chunks", review_chunks_node)
    graph.add_node("final_report", final_report_node)

    graph.add_edge(START, "load_diff")
    graph.add_edge("load_diff", "parse_diff")
    graph.add_edge("parse_diff", "review_chunks")
    graph.add_edge("review_chunks", "final_report")
    graph.add_edge("final_report", END)

    return graph.compile()


def run_review_graph(initial_state: ReviewGraphState) -> ReviewGraphState:
    graph = create_review_graph()
    return graph.invoke(initial_state)
