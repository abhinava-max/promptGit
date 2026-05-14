"""Create polished PDF review reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PURPLE = colors.HexColor("#7C3AED")
INDIGO = colors.HexColor("#6366F1")
MUTED = colors.HexColor("#64748B")
GREEN = colors.HexColor("#16A34A")
RED = colors.HexColor("#DC2626")
YELLOW = colors.HexColor("#CA8A04")
DARK = colors.HexColor("#111827")
LIGHT = colors.HexColor("#F8FAFC")
BORDER = colors.HexColor("#CBD5E1")


def title_case(value: str | None) -> str:
    if not value:
        return "Unknown"

    return str(value).replace("_", " ").title()


def severity_color(severity: str | None):
    severity_value = str(severity or "").upper()

    if severity_value in {"CRITICAL", "HIGH"}:
        return RED
    if severity_value == "MEDIUM":
        return YELLOW
    return GREEN


def recommendation_color(recommendation: str | None):
    recommendation_value = str(recommendation or "").upper()

    if recommendation_value == "REQUEST_CHANGES":
        return RED
    if recommendation_value == "NEEDS_MANUAL_REVIEW":
        return YELLOW
    return GREEN


def escape_text(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PromptGitXTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            textColor=PURPLE,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "subtitle": ParagraphStyle(
            "PromptGitXSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=18,
        ),
        "heading": ParagraphStyle(
            "PromptGitXHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=INDIGO,
            spaceBefore=12,
            spaceAfter=8,
        ),
        "normal": ParagraphStyle(
            "PromptGitXNormal",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=DARK,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "PromptGitXSmall",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
    }


def paragraph(text: str, style: ParagraphStyle):
    return Paragraph(text, style)


def section_title(text: str, styles: dict[str, ParagraphStyle]):
    return paragraph(escape_text(text), styles["heading"])


def key_value_table(rows: list[tuple[str, Any, Any]], styles: dict[str, ParagraphStyle]):
    table_rows = []

    for label, value, color in rows:
        value_style = ParagraphStyle(
            f"Value{label}",
            parent=styles["normal"],
            fontName="Helvetica-Bold" if color else "Helvetica",
            textColor=color or DARK,
        )
        table_rows.append(
            [
                paragraph(f"<b>{escape_text(label)}</b>", styles["normal"]),
                paragraph(escape_text(value), value_style),
            ]
        )

    table = Table(table_rows, colWidths=[1.8 * inch, 4.8 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def files_table(files: list[dict[str, Any]], styles: dict[str, ParagraphStyle]):
    rows = [
        [
            paragraph("<b>File</b>", styles["normal"]),
            paragraph("<b>Added</b>", styles["normal"]),
            paragraph("<b>Removed</b>", styles["normal"]),
        ]
    ]

    for file in files:
        rows.append(
            [
                paragraph(f"<font color='#16A34A'><b>{escape_text(file.get('file_path', 'unknown'))}</b></font>", styles["normal"]),
                paragraph(f"<font color='#16A34A'><b>+{file.get('added_lines', 0)}</b></font>", styles["normal"]),
                paragraph(f"<font color='#DC2626'><b>-{file.get('removed_lines', 0)}</b></font>", styles["normal"]),
            ]
        )

    if len(rows) == 1:
        rows.append([paragraph("None found.", styles["small"]), "", ""])

    table = Table(rows, colWidths=[4.6 * inch, 1.0 * inch, 1.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF2FF")),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def issue_section(title: str, items: list[dict[str, Any]], story: list, styles: dict[str, ParagraphStyle]):
    if not items:
        return

    story.append(section_title(title, styles))

    for item in items:
        text = (
            f"<font color='#16A34A'><b>{escape_text(item.get('file_path', 'unknown'))}</b></font>: "
            f"{escape_text(item.get('message') or item.get('suggestion') or 'No details provided.')}"
        )
        story.append(paragraph(text, styles["normal"]))

        if item.get("suggestion") and item.get("message"):
            story.append(paragraph(f"<font color='#64748B'><b>Suggestion:</b></font> {escape_text(item['suggestion'])}", styles["small"]))

        story.append(Spacer(1, 4))


def clean_checks(issues: dict[str, list[dict[str, Any]]], styles: dict[str, ParagraphStyle]):
    checks = [
        ("Critical", issues.get("critical", [])),
        ("Breaking", issues.get("breaking_changes", [])),
        ("Security", issues.get("security", [])),
        ("Unprofessional Language", issues.get("vulgarity", [])),
        ("Performance", issues.get("performance", [])),
    ]
    clean = [name for name, items in checks if not items]

    if clean:
        text = f"<font color='#64748B'><b>No findings in:</b></font> <font color='#16A34A'><b>{escape_text(', '.join(clean))}</b></font>"
    else:
        text = "<font color='#CA8A04'><b>Issues found in all major check groups.</b></font>"

    return paragraph(text, styles["normal"])


def file_wise_issues(files: list[dict[str, Any]], story: list, styles: dict[str, ParagraphStyle]):
    story.append(section_title("File-wise Issues", styles))
    found = False

    for file in files:
        for issue in file.get("issues", []):
            found = True
            severity = str(issue.get("severity", "low")).upper()
            color = severity_color(severity)
            rows = [
                [
                    paragraph(
                        f"<font color='#{color.hexval()[2:]}'><b>[{severity}]</b></font> "
                        f"<font color='#6366F1'><b>{escape_text(title_case(issue.get('category')))}</b></font>",
                        styles["normal"],
                    )
                ],
                [
                    paragraph(
                        f"<font color='#64748B'><b>File:</b></font> "
                        f"<font color='#16A34A'><b>{escape_text(file.get('file_path', 'unknown'))}</b></font>",
                        styles["normal"],
                    )
                ],
                [
                    paragraph(
                        f"<font color='#64748B'><b>Problem:</b></font> "
                        f"{escape_text(issue.get('message', 'No details provided.'))}",
                        styles["normal"],
                    )
                ],
            ]

            if issue.get("line_reference"):
                rows.append([paragraph(f"<font color='#64748B'><b>Reference:</b></font> {escape_text(issue['line_reference'])}", styles["normal"])])

            if issue.get("suggestion"):
                rows.append([paragraph(f"<font color='#64748B'><b>Suggestion:</b></font> {escape_text(issue['suggestion'])}", styles["normal"])])

            table = Table(rows, colWidths=[6.6 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                        ("BOX", (0, 0), (-1, -1), 1.0, color),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 8))

    if not found:
        story.append(paragraph("None found.", styles["small"]))


def create_pdf_report(report: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = build_styles()
    story = [
        paragraph("GitPromptX Review Report", styles["title"]),
        paragraph("AI-powered Git review summary", styles["subtitle"]),
    ]

    target = report.get("target", {})
    target_value = target.get("value", "")

    if isinstance(target_value, list):
        target_value = ", ".join(str(item) for item in target_value)

    story.append(section_title("Review Target", styles))
    story.append(
        key_value_table(
            [
                ("Mode", f"{title_case(target.get('mode'))} Review", None),
                ("Target", target_value, None),
            ],
            styles,
        )
    )

    summary = report.get("summary", {})
    recommendation = summary.get("final_recommendation", "APPROVE")
    risk = summary.get("risk_level", "low")
    story.append(section_title("Summary", styles))
    story.append(
        key_value_table(
            [
                ("Files Reviewed", summary.get("files_reviewed", 0), None),
                ("Lines Added", f"+{summary.get('lines_added', 0)}", GREEN),
                ("Lines Removed", f"-{summary.get('lines_removed', 0)}", RED),
                ("Overall Risk", title_case(risk), severity_color(risk)),
                ("Final Recommendation", recommendation, recommendation_color(recommendation)),
            ],
            styles,
        )
    )

    story.append(section_title("Files Changed", styles))
    story.append(files_table(report.get("files", []), styles))

    issues = report.get("issues", {})
    story.append(section_title("Clean Checks", styles))
    story.append(clean_checks(issues, styles))
    issue_section("Critical Issues", issues.get("critical", []), story, styles)
    issue_section("Breaking Changes", issues.get("breaking_changes", []), story, styles)
    issue_section("Security Concerns", issues.get("security", []), story, styles)
    issue_section("Code Quality Issues", issues.get("code_quality", []), story, styles)
    issue_section("Unprofessional Language", issues.get("vulgarity", []), story, styles)
    issue_section("Performance Issues", issues.get("performance", []), story, styles)
    issue_section("Improvement Suggestions", issues.get("improvements", []), story, styles)
    file_wise_issues(report.get("files", []), story, styles)

    story.append(section_title("Final Recommendation", styles))
    story.append(
        paragraph(
            f"<font color='#{recommendation_color(recommendation).hexval()[2:]}'><b>{escape_text(recommendation)}</b></font>",
            styles["heading"],
        )
    )
    story.append(paragraph(f"<font color='#64748B'><b>Reason:</b></font> {escape_text(report.get('overall_summary', 'No summary available.'))}", styles["normal"]))

    document.build(story)
