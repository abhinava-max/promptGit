"""LangGraph workflow for reviewing Git diffs."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, START, StateGraph

from .graph_state import ReviewGraphState
from .json_utils import extract_json_object, to_pretty_json
from .llm_provider import RuntimeModelRouter, get_current_model_display
from .report_builder import apply_refined_report, build_report, normalize_file_review
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
    split_large_diff_chunks,
    summarize_diff,
)
from ..gitcodes.git_info import get_current_branch, get_repo_root
from ..prompts import get_chunk_review_prompt, get_report_refinement_prompt


MAX_CHUNK_CHARS = 12000
MAX_NUMBERED_CHANGED_LINES = 120


def format_numbered_changed_lines(chunk: dict) -> str:
    changed_lines = chunk.get("changed_lines", [])

    if not changed_lines:
        return "No exact changed line references were parsed. Use file-level."

    lines = []

    for item in changed_lines[:MAX_NUMBERED_CHANGED_LINES]:
        prefix = "+" if item.get("kind") == "added" else "-"
        lines.append(f"{item.get('reference')}: {prefix} {item.get('content', '')}")

    remaining = len(changed_lines) - len(lines)

    if remaining > 0:
        lines.append(f"... {remaining} more changed line(s) omitted. Use file-level for omitted lines.")

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
    chunks = chunk_diff_by_file(diff)

    return {
        "diff_summary": summary,
        "chunks": chunks,
    }


def split_large_chunks_node(state: ReviewGraphState) -> ReviewGraphState:
    review_chunks = split_large_diff_chunks(
        state.get("chunks", []),
        max_chars=MAX_CHUNK_CHARS,
    )

    return {
        "review_chunks": review_chunks,
    }


def review_chunks_node(state: ReviewGraphState) -> ReviewGraphState:
    chunks = state.get("review_chunks", [])

    if not chunks:
        return {
            "chunk_reviews": [],
        }

    prompt = get_chunk_review_prompt()
    model_router = RuntimeModelRouter()
    chunk_reviews = []

    for index, chunk in enumerate(chunks, start=1):
        prompt_input = {
            "mode": state["mode"],
            "repo_context": state.get("repo_context", ""),
            "file_path": chunk.get("file_path", "unknown"),
            "chunk_part": chunk.get("chunk_part", 1),
            "chunk_total": chunk.get("chunk_total", 1),
            "added_lines_count": chunk.get("added_lines_count", 0),
            "removed_lines_count": chunk.get("removed_lines_count", 0),
            "numbered_changed_lines": format_numbered_changed_lines(chunk),
            "raw_diff": chunk.get("raw_diff", ""),
        }

        try:
            active_model = model_router.current_model
            chain = prompt | model_router.create_current_chat_model() | StrOutputParser()
            raw_review = chain.invoke(prompt_input)
        except Exception as error:
            while model_router.has_next_model():
                active_model = model_router.advance_model()
                chain = prompt | model_router.create_current_chat_model() | StrOutputParser()

                try:
                    raw_review = chain.invoke(prompt_input)
                    break
                except Exception as retry_error:
                    error = retry_error
            else:
                file_review = normalize_file_review(
                    {
                        "file_path": chunk.get("file_path", "unknown"),
                        "summary": "AI review failed for this file.",
                        "issues": [
                            {
                                "category": "maintainability",
                                "severity": "medium",
                                "line_reference": "file-level",
                                "message": f"AI review failed using all configured models: {error}",
                                "suggestion": "Run the review again or inspect this file manually.",
                            }
                        ],
                    },
                    chunk,
                )
                chunk_reviews.append(
                    {
                        "chunk": index,
                        "file_path": file_review["file_path"],
                        "chunk_part": chunk.get("chunk_part", 1),
                        "chunk_total": chunk.get("chunk_total", 1),
                        "parent_added_lines": chunk.get("parent_added_lines_count", file_review["added_lines"]),
                        "parent_removed_lines": chunk.get("parent_removed_lines_count", file_review["removed_lines"]),
                        "model": active_model.display_name,
                        "review": file_review,
                    }
                )
                continue

        try:
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

        chunk_reviews.append(
            {
                "chunk": index,
                "file_path": file_review["file_path"],
                "chunk_part": chunk.get("chunk_part", 1),
                "chunk_total": chunk.get("chunk_total", 1),
                "parent_added_lines": chunk.get("parent_added_lines_count", file_review["added_lines"]),
                "parent_removed_lines": chunk.get("parent_removed_lines_count", file_review["removed_lines"]),
                "model": active_model.display_name,
                "review": file_review,
            }
        )

    return {
        "chunk_reviews": chunk_reviews,
    }


def merge_file_reviews_node(state: ReviewGraphState) -> ReviewGraphState:
    grouped_reviews: dict[str, dict] = {}

    for chunk_review in state.get("chunk_reviews", []):
        review = chunk_review.get("review", {})
        file_path = str(chunk_review.get("file_path") or review.get("file_path", "unknown"))

        if file_path not in grouped_reviews:
            grouped_reviews[file_path] = {
                "file_path": file_path,
                "summary_parts": [],
                "added_lines": int(chunk_review.get("parent_added_lines", review.get("added_lines", 0))),
                "removed_lines": int(chunk_review.get("parent_removed_lines", review.get("removed_lines", 0))),
                "issues": [],
                "chunk_total": int(chunk_review.get("chunk_total", 1)),
            }

        summary = str(review.get("summary", "")).strip()

        if summary and summary not in grouped_reviews[file_path]["summary_parts"]:
            grouped_reviews[file_path]["summary_parts"].append(summary)

        grouped_reviews[file_path]["issues"].extend(review.get("issues", []))
        grouped_reviews[file_path]["chunk_total"] = max(
            grouped_reviews[file_path]["chunk_total"],
            int(chunk_review.get("chunk_total", 1)),
        )

    file_reviews = []

    for grouped in grouped_reviews.values():
        summary_parts = grouped.pop("summary_parts")
        chunk_total = grouped.pop("chunk_total")

        if not summary_parts:
            summary = ""
        elif chunk_total > 1:
            summary = f"Reviewed in {chunk_total} parts. " + " ".join(summary_parts)
        else:
            summary = summary_parts[0]

        file_reviews.append(
            {
                "file_path": grouped["file_path"],
                "summary": summary,
                "added_lines": grouped["added_lines"],
                "removed_lines": grouped["removed_lines"],
                "issues": grouped["issues"],
            }
        )

    return {
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


def refine_report_node(state: ReviewGraphState) -> ReviewGraphState:
    report = state.get("report", {})

    if not report:
        return {}

    prompt = get_report_refinement_prompt()
    model_router = RuntimeModelRouter()
    prompt_input = {
        "report_json": to_pretty_json(report),
    }

    try:
        active_model = model_router.current_model
        chain = prompt | model_router.create_current_chat_model() | StrOutputParser()
        raw_refined_report = chain.invoke(prompt_input)
    except Exception as error:
        while model_router.has_next_model():
            active_model = model_router.advance_model()
            chain = prompt | model_router.create_current_chat_model() | StrOutputParser()

            try:
                raw_refined_report = chain.invoke(prompt_input)
                break
            except Exception as retry_error:
                error = retry_error
        else:
            return {
                "report": {
                    **report,
                    "refinement_error": f"Final report refinement failed using all configured models: {error}",
                },
                "final_report": to_pretty_json(
                    {
                        **report,
                        "refinement_error": f"Final report refinement failed using all configured models: {error}",
                    }
                ),
            }

    try:
        parsed_refined_report = extract_json_object(raw_refined_report)
        refined_report = apply_refined_report(report, parsed_refined_report)
        refined_report["refined_by_model"] = active_model.display_name
    except Exception as error:
        refined_report = {
            **report,
            "refinement_error": f"Final report refinement output could not be parsed: {error}",
        }

    return {
        "report": refined_report,
        "final_report": to_pretty_json(refined_report),
    }


def create_review_graph():
    graph = StateGraph(ReviewGraphState)
    graph.add_node("load_diff", load_diff_node)
    graph.add_node("parse_diff", parse_diff_node)
    graph.add_node("split_large_chunks", split_large_chunks_node)
    graph.add_node("review_chunks", review_chunks_node)
    graph.add_node("merge_file_reviews", merge_file_reviews_node)
    graph.add_node("final_report", final_report_node)
    graph.add_node("refine_report", refine_report_node)

    graph.add_edge(START, "load_diff")
    graph.add_edge("load_diff", "parse_diff")
    graph.add_edge("parse_diff", "split_large_chunks")
    graph.add_edge("split_large_chunks", "review_chunks")
    graph.add_edge("review_chunks", "merge_file_reviews")
    graph.add_edge("merge_file_reviews", "final_report")
    graph.add_edge("final_report", "refine_report")
    graph.add_edge("refine_report", END)

    return graph.compile()


def run_review_graph(initial_state: ReviewGraphState) -> ReviewGraphState:
    graph = create_review_graph()
    return graph.invoke(initial_state)
