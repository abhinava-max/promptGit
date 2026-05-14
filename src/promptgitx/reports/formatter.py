"""Format structured review reports for terminal output."""

from __future__ import annotations

from typing import Any

from rich.text import Text


LINE = "-" * 48
STYLE_TITLE = "bold #c084fc"
STYLE_SECTION = "bold #818cf8"
STYLE_LABEL = "bold #94a3b8"
STYLE_MUTED = "#64748b"
STYLE_FILE = "bold #22c55e"
STYLE_ADDED = "bold #22c55e"
STYLE_REMOVED = "bold #fb7185"
STYLE_RED = "bold #fb7185"
STYLE_YELLOW = "bold #facc15"
STYLE_GREEN = "bold #22c55e"


def title_case(value: str | None) -> str:
    if not value:
        return "Unknown"

    return str(value).replace("_", " ").title()


def uppercase(value: str | None) -> str:
    return str(value or "").upper()


def severity_style(severity: str | None) -> str:
    severity_value = uppercase(severity)

    if severity_value in {"CRITICAL", "HIGH"}:
        return STYLE_RED
    if severity_value == "MEDIUM":
        return STYLE_YELLOW
    return STYLE_GREEN


def recommendation_style(recommendation: str | None) -> str:
    recommendation_value = uppercase(recommendation)

    if recommendation_value == "REQUEST_CHANGES":
        return STYLE_RED
    if recommendation_value == "NEEDS_MANUAL_REVIEW":
        return STYLE_YELLOW
    return STYLE_GREEN


def risk_style(risk_level: str | None) -> str:
    risk_value = str(risk_level or "").lower()

    if risk_value in {"critical", "high"}:
        return STYLE_RED
    if risk_value == "medium":
        return STYLE_YELLOW
    return STYLE_GREEN


def append_label(text: Text, label: str):
    text.append(label, style=STYLE_LABEL)


def append_file(text: Text, file_path: str):
    text.append(file_path, style=STYLE_FILE)


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


def render_header(title: str) -> Text:
    text = Text()
    text.append(f"{LINE}\n", style=STYLE_MUTED)
    text.append(f"{title}\n", style=STYLE_TITLE)
    text.append(LINE, style=STYLE_MUTED)
    return text


def render_target(report: dict[str, Any]) -> Text:
    target = report.get("target", {})
    mode = target.get("mode", "unknown")
    value = target.get("value")
    text = Text()
    text.append("Target:\n", style=STYLE_SECTION)
    append_label(text, "Mode: ")
    text.append(f"{title_case(mode)} Review\n")

    if value is not None:
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        append_label(text, "Target: ")
        text.append(str(value))

    return text


def render_summary(report: dict[str, Any]) -> Text:
    summary = report.get("summary", {})
    risk_level = summary.get("risk_level", "low")
    recommendation = summary.get("final_recommendation", "APPROVE")
    text = Text()
    text.append("Summary:\n", style=STYLE_SECTION)
    append_label(text, "Files Reviewed: ")
    text.append(f"{summary.get('files_reviewed', 0)}\n")
    append_label(text, "Lines Added: ")
    text.append(f"{summary.get('lines_added', 0)}\n", style=STYLE_ADDED)
    append_label(text, "Lines Removed: ")
    text.append(f"{summary.get('lines_removed', 0)}\n", style=STYLE_REMOVED)
    append_label(text, "Overall Risk: ")
    text.append(f"{title_case(risk_level)}\n", style=risk_style(risk_level))
    append_label(text, "Final Recommendation: ")
    text.append(uppercase(recommendation), style=recommendation_style(recommendation))
    return text


def render_files_changed(report: dict[str, Any]) -> Text:
    files = report.get("files", [])
    text = Text()
    text.append("Files Changed:\n", style=STYLE_SECTION)

    if not files:
        text.append("- None found.", style=STYLE_MUTED)
        return text

    for index, file in enumerate(files):
        if index:
            text.append("\n")
        text.append("- ")
        append_file(text, str(file.get("file_path", "unknown")))
        text.append(" (")
        text.append(f"+{file.get('added_lines', 0)}", style=STYLE_ADDED)
        text.append(" / ")
        text.append(f"-{file.get('removed_lines', 0)}", style=STYLE_REMOVED)
        text.append(")")

    return text


def render_issue_items(title: str, items: list[dict[str, Any]]) -> Text:
    text = Text()
    text.append(f"{title}:\n", style=STYLE_SECTION)

    if not items:
        text.append("- None found.", style=STYLE_MUTED)
        return text

    for index, item in enumerate(items):
        if index:
            text.append("\n")
        text.append("- ")
        append_file(text, str(item.get("file_path", "unknown")))
        text.append(": ")
        text.append(str(item.get("message") or item.get("suggestion") or "No details provided."))

        if item.get("suggestion") and item.get("message"):
            text.append("\n  ")
            append_label(text, "Suggestion: ")
            text.append(str(item["suggestion"]))

    return text


def render_file_wise_issues(report: dict[str, Any]) -> Text:
    text = Text()
    text.append("File-wise Issues:\n", style=STYLE_SECTION)
    files = report.get("files", [])
    has_issues = False

    for file in files:
        for issue in file.get("issues", []):
            if has_issues:
                text.append("\n")
            has_issues = True
            severity = uppercase(issue.get("severity"))
            text.append("- [")
            text.append(severity, style=severity_style(severity))
            text.append("] ")
            text.append(title_case(issue.get("category")), style=STYLE_LABEL)
            text.append("\n  ")
            append_label(text, "File: ")
            append_file(text, str(file.get("file_path", "unknown")))
            text.append("\n  ")
            append_label(text, "Problem: ")
            text.append(str(issue.get("message", "No details provided.")))

            if issue.get("line_reference"):
                text.append("\n  ")
                append_label(text, "Reference: ")
                text.append(str(issue["line_reference"]))

            if issue.get("suggestion"):
                text.append("\n  ")
                append_label(text, "Suggestion: ")
                text.append(str(issue["suggestion"]))

    if not has_issues:
        text.append("- None found.", style=STYLE_MUTED)

    return text


def render_final(report: dict[str, Any]) -> Text:
    summary = report.get("summary", {})
    recommendation = summary.get("final_recommendation", "APPROVE")
    text = Text()
    text.append("Final:\n", style=STYLE_SECTION)
    text.append(f"{uppercase(recommendation)}\n", style=recommendation_style(recommendation))
    append_label(text, "Reason: ")
    text.append(str(report.get("overall_summary", "No summary available.")))
    return text


def join_rich_sections(sections: list[Text]) -> Text:
    output = Text()

    for index, section in enumerate(sections):
        if index:
            output.append("\n\n")
        output.append_text(section)

    return output


def render_terminal_report(report: dict[str, Any]) -> Text:
    issues = report.get("issues", {})
    return join_rich_sections(
        [
            render_header("GitPromptX Review Report"),
            render_target(report),
            render_summary(report),
            render_files_changed(report),
            render_issue_items("Critical Issues", issues.get("critical", [])),
            render_issue_items("Breaking Changes", issues.get("breaking_changes", [])),
            render_issue_items("Security Concerns", issues.get("security", [])),
            render_issue_items("Code Quality Issues", issues.get("code_quality", [])),
            render_issue_items("Unprofessional Language", issues.get("vulgarity", [])),
            render_issue_items("Performance Issues", issues.get("performance", [])),
            render_file_wise_issues(report),
            render_issue_items("Improvement Suggestions", issues.get("improvements", [])),
            render_final(report),
        ]
    )


def render_summary_report(report: dict[str, Any]) -> Text:
    return join_rich_sections(
        [
            render_header("GitPromptX Review Summary"),
            render_target(report),
            render_summary(report),
            render_final(report),
        ]
    )
