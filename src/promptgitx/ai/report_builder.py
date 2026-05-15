"""Build structured review reports from per-file AI reviews."""

from __future__ import annotations

import re
from typing import Any


ALLOWED_CATEGORIES = {
    "bug",
    "breaking_change",
    "security",
    "performance",
    "code_quality",
    "vulgarity",
    "standards",
    "testing",
    "documentation",
    "maintainability",
}

ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def build_target(state: dict[str, Any]) -> dict[str, Any]:
    mode = state["mode"]
    value = None

    if mode == "commit":
        value = state.get("commit")
    elif mode == "commits":
        value = state.get("commits") or []
    elif mode == "compare":
        value = state.get("compare")
    elif mode == "pr":
        value = f"#{state.get('pr')}"
    elif mode == "last":
        value = "HEAD"
    elif mode == "last_n":
        value = state.get("last_n")
    elif mode == "staged":
        value = "staged changes"

    return {"mode": mode, "value": value}


def compact_line_reference(file_path: str, prefix: str, line_numbers: list[int]) -> str:
    unique_numbers = sorted(set(line_numbers))

    if not unique_numbers:
        return "changed block"

    label = "old L" if prefix == "old" else "L"

    if len(unique_numbers) == 1:
        return f"{file_path}:{label}{unique_numbers[0]}"

    if unique_numbers == list(range(unique_numbers[0], unique_numbers[-1] + 1)):
        return f"{file_path}:{label}{unique_numbers[0]}-{label}{unique_numbers[-1]}"

    return ", ".join(f"{file_path}:{label}{line_number}" for line_number in unique_numbers[:3])


def normalize_line_reference(reference: Any, chunk: dict[str, Any]) -> str:
    reference_text = str(reference or "").strip()
    changed_lines = chunk.get("changed_lines", [])

    if not reference_text or reference_text.lower() in {"changed block", "unknown", "n/a", "none"}:
        return "changed block"

    valid_references = {
        str(item.get("reference", "")).strip()
        for item in changed_lines
        if item.get("reference")
    }

    if reference_text in valid_references:
        return reference_text

    file_path = str(chunk.get("file_path", "unknown"))
    new_lines = {
        int(item["line_number"])
        for item in changed_lines
        if item.get("kind") == "added" and item.get("line_number") is not None
    }
    old_lines = {
        int(item["line_number"])
        for item in changed_lines
        if item.get("kind") == "removed" and item.get("line_number") is not None
    }
    reference_numbers = [int(match) for match in re.findall(r"(?:line\s*|L)(\d+)", reference_text, flags=re.IGNORECASE)]

    if not reference_numbers:
        return "changed block"

    is_old_reference = "old" in reference_text.lower() or "removed" in reference_text.lower()
    matching_old_lines = [line_number for line_number in reference_numbers if line_number in old_lines]
    matching_new_lines = [line_number for line_number in reference_numbers if line_number in new_lines]

    if is_old_reference and matching_old_lines:
        return compact_line_reference(file_path, "old", matching_old_lines)

    if matching_new_lines:
        return compact_line_reference(file_path, "new", matching_new_lines)

    if matching_old_lines:
        return compact_line_reference(file_path, "old", matching_old_lines)

    return "changed block"


def normalize_issue(issue: dict[str, Any], chunk: dict[str, Any]) -> dict[str, str]:
    category = str(issue.get("category", "maintainability")).strip().lower()
    severity = str(issue.get("severity", "medium")).strip().lower()

    if category not in ALLOWED_CATEGORIES:
        category = "maintainability"

    if severity not in ALLOWED_SEVERITIES:
        severity = "medium"

    return {
        "category": category,
        "severity": severity,
        "line_reference": normalize_line_reference(issue.get("line_reference", "changed block"), chunk),
        "message": str(issue.get("message", "")).strip(),
        "suggestion": str(issue.get("suggestion", "")).strip(),
    }


def normalize_file_review(
    file_review: dict[str, Any],
    chunk: dict[str, Any],
) -> dict[str, Any]:
    raw_issues = file_review.get("issues", [])

    if not isinstance(raw_issues, list):
        raw_issues = []

    return {
        "file_path": str(file_review.get("file_path") or chunk.get("file_path", "unknown")),
        "summary": str(file_review.get("summary", "")).strip(),
        "added_lines": int(chunk.get("added_lines_count", 0)),
        "removed_lines": int(chunk.get("removed_lines_count", 0)),
        "issues": [
            normalize_issue(issue, chunk)
            for issue in raw_issues
            if isinstance(issue, dict) and str(issue.get("message", "")).strip()
        ],
    }


def issue_item(file_path: str, issue: dict[str, str]) -> dict[str, str]:
    return {
        "file_path": file_path,
        "line_reference": issue["line_reference"],
        "message": issue["message"],
        "suggestion": issue["suggestion"],
    }


def calculate_risk(files: list[dict[str, Any]]) -> str:
    max_rank = 0

    for file in files:
        for issue in file["issues"]:
            max_rank = max(max_rank, SEVERITY_RANK[issue["severity"]])

    if max_rank >= SEVERITY_RANK["critical"]:
        return "critical"
    if max_rank >= SEVERITY_RANK["high"]:
        return "high"
    if max_rank >= SEVERITY_RANK["medium"]:
        return "medium"
    return "low"


def calculate_recommendation(risk_level: str, files: list[dict[str, Any]]) -> str:
    if risk_level in {"high", "critical"}:
        return "REQUEST_CHANGES"

    has_uncertain_review = any(
        issue["category"] in {"security", "breaking_change", "testing"}
        for file in files
        for issue in file["issues"]
    )

    if risk_level == "medium" or has_uncertain_review:
        return "NEEDS_MANUAL_REVIEW"

    return "APPROVE"


def build_overall_summary(files: list[dict[str, Any]]) -> str:
    if not files:
        return "No code changes were found for this review target."

    issue_count = sum(len(file["issues"]) for file in files)

    if issue_count == 0:
        return f"Reviewed {len(files)} changed file(s). No issues were detected."

    return f"Reviewed {len(files)} changed file(s) and found {issue_count} issue(s)."


def build_report(
    *,
    state: dict[str, Any],
    file_reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = state.get("diff_summary", {})
    risk_level = calculate_risk(file_reviews)
    recommendation = calculate_recommendation(risk_level, file_reviews)

    issues = {
        "critical": [],
        "security": [],
        "breaking_changes": [],
        "vulgarity": [],
        "performance": [],
        "code_quality": [],
        "improvements": [],
    }

    for file in file_reviews:
        file_path = file["file_path"]

        for issue in file["issues"]:
            item = issue_item(file_path, issue)

            if issue["severity"] == "critical":
                issues["critical"].append(item)
            if issue["category"] == "security":
                issues["security"].append(item)
            if issue["category"] == "breaking_change":
                issues["breaking_changes"].append(item)
            if issue["category"] == "vulgarity":
                issues["vulgarity"].append(item)
            if issue["category"] == "performance":
                issues["performance"].append(item)
            if issue["category"] in {"bug", "code_quality", "standards", "testing", "documentation", "maintainability"}:
                issues["code_quality"].append(item)
            if issue["suggestion"]:
                issues["improvements"].append(
                    {
                        "file_path": file_path,
                        "line_reference": issue["line_reference"],
                        "suggestion": issue["suggestion"],
                    }
                )

    return {
        "target": build_target(state),
        "overall_summary": build_overall_summary(file_reviews),
        "summary": {
            "files_reviewed": int(summary.get("total_files", len(file_reviews))),
            "lines_added": int(summary.get("total_added_lines", 0)),
            "lines_removed": int(summary.get("total_removed_lines", 0)),
            "risk_level": risk_level,
            "final_recommendation": recommendation,
        },
        "files": file_reviews,
        "issues": issues,
    }
