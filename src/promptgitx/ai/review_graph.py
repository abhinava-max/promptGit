"""LangGraph workflow for reviewing Git diffs."""

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph

from .graph_state import ReviewGraphState
from .llm_provider import create_chat_model_with_fallbacks, get_current_model_display
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
from ..prompts import get_chunk_review_prompt, get_final_review_prompt


MAX_CHUNK_CHARS = 12000


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


def format_diff_summary(summary: dict[str, Any]) -> str:
    files = summary.get("files", [])
    file_lines = [
        f"- {file['file_path']}: +{file['added_lines']} -{file['removed_lines']}"
        for file in files
    ]

    header = (
        f"Files changed: {summary.get('total_files', 0)}\n"
        f"Added lines: {summary.get('total_added_lines', 0)}\n"
        f"Removed lines: {summary.get('total_removed_lines', 0)}"
    )

    if not file_lines:
        return header

    return f"{header}\n\nFiles:\n" + "\n".join(file_lines)


def format_chunk(chunk: dict[str, Any]) -> str:
    trimmed_note = "\n\n[Diff trimmed for model context.]" if chunk.get("was_trimmed") else ""

    return (
        f"File: {chunk.get('file_path', 'unknown')}\n"
        f"Added lines: {chunk.get('added_lines_count', 0)}\n"
        f"Removed lines: {chunk.get('removed_lines_count', 0)}\n\n"
        f"{chunk.get('raw_diff', '')}"
        f"{trimmed_note}"
    )


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
        return {"chunk_reviews": ["No code changes were found in the selected diff."]}

    chain = get_chunk_review_prompt() | create_chat_model_with_fallbacks() | StrOutputParser()
    diff_summary = format_diff_summary(state.get("diff_summary", {}))
    chunk_reviews = []

    for index, chunk in enumerate(chunks, start=1):
        review = chain.invoke(
            {
                "mode": state["mode"],
                "repo_context": state.get("repo_context", ""),
                "diff_summary": diff_summary,
                "diff_chunk": format_chunk(chunk),
            }
        )
        chunk_reviews.append(f"## Chunk {index}: {chunk.get('file_path', 'unknown')}\n{review}")

    return {"chunk_reviews": chunk_reviews}


def final_report_node(state: ReviewGraphState) -> ReviewGraphState:
    if not state.get("chunks"):
        return {
            "final_report": (
                "No code changes were found for this selection.\n\n"
                "There is nothing to review yet."
            )
        }

    chain = get_final_review_prompt() | create_chat_model_with_fallbacks() | StrOutputParser()
    report = chain.invoke(
        {
            "mode": state["mode"],
            "model_name": state.get("model_name", get_current_model_display()),
            "diff_summary": format_diff_summary(state.get("diff_summary", {})),
            "chunk_reviews": "\n\n".join(state.get("chunk_reviews", [])),
        }
    )

    return {"final_report": report}


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
