"""Format structured review reports for terminal output."""

from __future__ import annotations

from typing import Any

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
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
STYLE_BORDER = "#6366f1"


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
    text = Text(title, style=STYLE_TITLE, justify="center")
    return Panel(
        text,
        border_style=STYLE_BORDER,
        padding=(1, 2),
    )


def render_target(report: dict[str, Any]) -> Text:
    target = report.get("target", {})
    mode = target.get("mode", "unknown")
    value = target.get("value")
    text = Text()
    append_label(text, "Mode: ")
    text.append(f"{title_case(mode)} Review\n")

    if value is not None:
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        append_label(text, "Target: ")
        text.append(str(value))

    return Panel(
        text,
        title="[bold #c084fc]Review Target[/bold #c084fc]",
        border_style=STYLE_BORDER,
        padding=(1, 2),
    )


def render_summary(report: dict[str, Any]) -> Text:
    summary = report.get("summary", {})
    risk_level = summary.get("risk_level", "low")
    recommendation = summary.get("final_recommendation", "APPROVE")
    table = Table(
        show_header=False,
        box=None,
        expand=True,
        padding=(0, 2),
    )
    table.add_column("Metric", style=STYLE_LABEL, ratio=2)
    table.add_column("Value", ratio=3)
    table.add_row("Files Reviewed", str(summary.get("files_reviewed", 0)))
    table.add_row("Lines Added", Text(f"+{summary.get('lines_added', 0)}", style=STYLE_ADDED))
    table.add_row("Lines Removed", Text(f"-{summary.get('lines_removed', 0)}", style=STYLE_REMOVED))
    table.add_row("Overall Risk", Text(title_case(risk_level), style=risk_style(risk_level)))
    table.add_row(
        "Final Recommendation",
        Text(uppercase(recommendation), style=recommendation_style(recommendation)),
    )
    return Panel(
        table,
        title="[bold #c084fc]Summary[/bold #c084fc]",
        border_style=STYLE_BORDER,
        padding=(1, 2),
    )


def render_files_changed(report: dict[str, Any]) -> Text:
    files = report.get("files", [])

    if not files:
        return Panel(
            Text("None found.", style=STYLE_MUTED),
            title="[bold #c084fc]Files Changed[/bold #c084fc]",
            border_style=STYLE_BORDER,
            padding=(1, 2),
        )

    table = Table(
        show_header=True,
        header_style=STYLE_LABEL,
        border_style=STYLE_MUTED,
        expand=True,
        box=None,
    )
    table.add_column("File")
    table.add_column("Added", justify="right")
    table.add_column("Removed", justify="right")

    for file in files:
        table.add_row(
            Text(str(file.get("file_path", "unknown")), style=STYLE_FILE),
            Text(f"+{file.get('added_lines', 0)}", style=STYLE_ADDED),
            Text(f"-{file.get('removed_lines', 0)}", style=STYLE_REMOVED),
        )

    return Panel(
        table,
        title="[bold #c084fc]Files Changed[/bold #c084fc]",
        border_style=STYLE_BORDER,
        padding=(1, 2),
    )


def render_issue_items(title: str, items: list[dict[str, Any]]) -> Text:
    text = Text()

    if not items:
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


def get_clean_checks(report: dict[str, Any]) -> list[str]:
    issues = report.get("issues", {})
    checks = [
        ("Critical", issues.get("critical", [])),
        ("Breaking", issues.get("breaking_changes", [])),
        ("Security", issues.get("security", [])),
        ("Unprofessional Language", issues.get("vulgarity", [])),
        ("Performance", issues.get("performance", [])),
    ]
    return [name for name, items in checks if not items]


def render_clean_checks(report: dict[str, Any]) -> Panel:
    clean_checks = get_clean_checks(report)

    if not clean_checks:
        text = Text("Issues found in all major check groups.", style=STYLE_YELLOW)
    else:
        text = Text()
        text.append("No findings in: ", style=STYLE_LABEL)
        text.append(", ".join(clean_checks), style=STYLE_GREEN)

    return Panel(
        text,
        title="[bold #c084fc]Clean Checks[/bold #c084fc]",
        border_style=STYLE_BORDER,
        padding=(1, 2),
    )


def render_issue_group(title: str, items: list[dict[str, Any]], style: str = STYLE_SECTION):
    if not items:
        return None

    table = Table.grid(expand=True)
    table.add_column()

    for item in items:
        line = Text()
        append_file(line, str(item.get("file_path", "unknown")))
        line.append(": ")
        line.append(str(item.get("message") or item.get("suggestion") or "No details provided."))

        if item.get("suggestion") and item.get("message"):
            line.append("\n")
            append_label(line, "Suggestion: ")
            line.append(str(item["suggestion"]))

        table.add_row(line)

    return Panel(
        table,
        title=f"[{style}]{title}[/{style}]",
        border_style=STYLE_BORDER,
        padding=(1, 2),
    )


def render_file_wise_issues(report: dict[str, Any]) -> Text:
    files = report.get("files", [])
    issue_panels = []
    has_issues = False

    for file in files:
        for issue in file.get("issues", []):
            has_issues = True
            severity = uppercase(issue.get("severity"))
            body = Text()
            body.append("[")
            body.append(severity, style=severity_style(severity))
            body.append("] ")
            body.append(title_case(issue.get("category")), style=STYLE_LABEL)
            body.append("\n")
            append_label(body, "File: ")
            append_file(body, str(file.get("file_path", "unknown")))
            body.append("\n")
            append_label(body, "Problem: ")
            body.append(str(issue.get("message", "No details provided.")))

            if issue.get("line_reference"):
                body.append("\n")
                append_label(body, "Reference: ")
                body.append(str(issue["line_reference"]))

            if issue.get("suggestion"):
                body.append("\n")
                append_label(body, "Suggestion: ")
                body.append(str(issue["suggestion"]))

            issue_panels.append(
                Panel(
                    body,
                    border_style=severity_style(severity),
                    padding=(1, 2),
                )
            )

    if not has_issues:
        return Panel(
            Text("None found.", style=STYLE_MUTED),
            title="[bold #c084fc]File-wise Issues[/bold #c084fc]",
            border_style=STYLE_BORDER,
            padding=(1, 2),
        )

    return Panel(
        Group(*issue_panels),
        title="[bold #c084fc]File-wise Issues[/bold #c084fc]",
        border_style=STYLE_BORDER,
        padding=(1, 1),
    )


def render_final(report: dict[str, Any]) -> Text:
    summary = report.get("summary", {})
    recommendation = summary.get("final_recommendation", "APPROVE")
    text = Text()
    text.append(f"{uppercase(recommendation)}\n", style=recommendation_style(recommendation))
    append_label(text, "Reason: ")
    text.append(str(report.get("overall_summary", "No summary available.")))
    return Panel(
        text,
        title="[bold #c084fc]Final Recommendation[/bold #c084fc]",
        border_style=recommendation_style(recommendation),
        padding=(1, 2),
    )


def render_terminal_report(report: dict[str, Any]) -> Group:
    issues = report.get("issues", {})
    optional_sections = [
        render_issue_group("Critical Issues", issues.get("critical", []), STYLE_RED),
        render_issue_group("Breaking Changes", issues.get("breaking_changes", []), STYLE_RED),
        render_issue_group("Security Concerns", issues.get("security", []), STYLE_RED),
        render_issue_group("Code Quality Issues", issues.get("code_quality", []), STYLE_YELLOW),
        render_issue_group("Unprofessional Language", issues.get("vulgarity", []), STYLE_YELLOW),
        render_issue_group("Performance Issues", issues.get("performance", []), STYLE_YELLOW),
        render_issue_group("Improvement Suggestions", issues.get("improvements", []), STYLE_GREEN),
    ]
    sections = [
        render_header("GitPromptX Review Report"),
        render_target(report),
        render_summary(report),
        render_files_changed(report),
        render_clean_checks(report),
    ]
    sections.extend(section for section in optional_sections if section is not None)
    sections.extend(
        [
            render_file_wise_issues(report),
            render_final(report),
        ]
    )

    return Group(*sections)


def render_summary_report(report: dict[str, Any]) -> Group:
    return Group(
            render_header("GitPromptX Review Summary"),
            render_target(report),
            render_summary(report),
            render_final(report),
    )
