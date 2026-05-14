"""Format structured review reports for terminal output."""

from __future__ import annotations

from typing import Any


LINE = "-" * 48


def title_case(value: str | None) -> str:
    if not value:
        return "Unknown"

    return str(value).replace("_", " ").title()


def uppercase(value: str | None) -> str:
    return str(value or "").upper()


def format_target(report: dict[str, Any]) -> list[str]:
    target = report.get("target", {})
    mode = target.get("mode", "unknown")
    value = target.get("value")
    lines = [
        "Target:",
        f"Mode: {title_case(mode)} Review",
    ]

    if value is not None:
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        lines.append(f"Target: {value}")

    return lines


def format_summary(report: dict[str, Any]) -> list[str]:
    summary = report.get("summary", {})

    return [
        "Summary:",
        f"Files Reviewed: {summary.get('files_reviewed', 0)}",
        f"Lines Added: {summary.get('lines_added', 0)}",
        f"Lines Removed: {summary.get('lines_removed', 0)}",
        f"Overall Risk: {title_case(summary.get('risk_level', 'low'))}",
        f"Final Recommendation: {uppercase(summary.get('final_recommendation', 'APPROVE'))}",
    ]


def format_files_changed(report: dict[str, Any]) -> list[str]:
    files = report.get("files", [])
    lines = ["Files Changed:"]

    if not files:
        return lines + ["- None found."]

    for file in files:
        lines.append(
            f"- {file.get('file_path', 'unknown')} "
            f"(+{file.get('added_lines', 0)} / -{file.get('removed_lines', 0)})"
        )

    return lines


def format_issue_items(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"{title}:"]

    if not items:
        return lines + ["- None found."]

    for item in items:
        file_path = item.get("file_path", "unknown")
        has_message = bool(item.get("message"))
        message = item.get("message") or item.get("suggestion") or "No details provided."
        suggestion = item.get("suggestion")
        lines.append(f"- {file_path}: {message}")

        if suggestion and has_message:
            lines.append(f"  Suggestion: {suggestion}")

    return lines


def format_file_wise_issues(report: dict[str, Any]) -> list[str]:
    lines = ["File-wise Issues:"]
    files = report.get("files", [])
    has_issues = False

    for file in files:
        for issue in file.get("issues", []):
            has_issues = True
            lines.append(f"- [{uppercase(issue.get('severity'))}] {title_case(issue.get('category'))}")
            lines.append(f"  File: {file.get('file_path', 'unknown')}")
            lines.append(f"  Problem: {issue.get('message', 'No details provided.')}")

            if issue.get("line_reference"):
                lines.append(f"  Reference: {issue['line_reference']}")

            if issue.get("suggestion"):
                lines.append(f"  Suggestion: {issue['suggestion']}")

    if not has_issues:
        lines.append("- None found.")

    return lines


def format_final(report: dict[str, Any]) -> list[str]:
    summary = report.get("summary", {})

    return [
        "Final:",
        uppercase(summary.get("final_recommendation", "APPROVE")),
        f"Reason: {report.get('overall_summary', 'No summary available.')}",
    ]


def join_sections(sections: list[list[str]]) -> str:
    return "\n\n".join("\n".join(section) for section in sections)


def format_terminal_report(report: dict[str, Any]) -> str:
    issues = report.get("issues", {})
    sections = [
        [
            LINE,
            "GitPromptX Review Report",
            LINE,
        ],
        format_target(report),
        format_summary(report),
        format_files_changed(report),
        format_issue_items("Critical Issues", issues.get("critical", [])),
        format_issue_items("Breaking Changes", issues.get("breaking_changes", [])),
        format_issue_items("Security Concerns", issues.get("security", [])),
        format_issue_items("Code Quality Issues", issues.get("code_quality", [])),
        format_issue_items("Unprofessional Language", issues.get("vulgarity", [])),
        format_issue_items("Performance Issues", issues.get("performance", [])),
        format_file_wise_issues(report),
        format_issue_items("Improvement Suggestions", issues.get("improvements", [])),
        format_final(report),
    ]

    return join_sections(sections)


def format_summary_report(report: dict[str, Any]) -> str:
    sections = [
        [
            LINE,
            "GitPromptX Review Summary",
            LINE,
        ],
        format_target(report),
        format_summary(report),
        format_final(report),
    ]

    return join_sections(sections)
