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
ISSUE_INDEX_KEYS = (
    "critical",
    "security",
    "breaking_changes",
    "vulgarity",
    "performance",
    "bug",
    "code_quality",
    "standards",
    "testing",
    "documentation",
    "maintainability",
    "improvements",
)


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
        return f"{file_path}:changed lines"

    label = "old L" if prefix == "old" else "L"

    if len(unique_numbers) == 1:
        return f"{file_path}:{label}{unique_numbers[0]}"

    if unique_numbers == list(range(unique_numbers[0], unique_numbers[-1] + 1)):
        return f"{file_path}:{label}{unique_numbers[0]}-{label}{unique_numbers[-1]}"

    return ", ".join(f"{file_path}:{label}{line_number}" for line_number in unique_numbers[:3])


def fallback_line_reference(chunk: dict[str, Any]) -> str:
    file_path = str(chunk.get("file_path", "unknown"))
    changed_lines = chunk.get("changed_lines", [])
    added_lines = [
        int(item["line_number"])
        for item in changed_lines
        if item.get("kind") == "added" and item.get("line_number") is not None
    ]
    removed_lines = [
        int(item["line_number"])
        for item in changed_lines
        if item.get("kind") == "removed" and item.get("line_number") is not None
    ]

    if added_lines:
        return compact_line_reference(file_path, "new", added_lines)

    if removed_lines:
        return compact_line_reference(file_path, "old", removed_lines)

    return f"{file_path}:changed file"


def normalize_line_reference(reference: Any, chunk: dict[str, Any]) -> str:
    reference_text = str(reference or "").strip()
    changed_lines = chunk.get("changed_lines", [])

    if not reference_text or reference_text.lower() in {"changed block", "changed lines", "file-level", "unknown", "n/a", "none"}:
        return fallback_line_reference(chunk)

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
        return fallback_line_reference(chunk)

    is_old_reference = "old" in reference_text.lower() or "removed" in reference_text.lower()
    matching_old_lines = [line_number for line_number in reference_numbers if line_number in old_lines]
    matching_new_lines = [line_number for line_number in reference_numbers if line_number in new_lines]

    if is_old_reference and matching_old_lines:
        return compact_line_reference(file_path, "old", matching_old_lines)

    if matching_new_lines:
        return compact_line_reference(file_path, "new", matching_new_lines)

    if matching_old_lines:
        return compact_line_reference(file_path, "old", matching_old_lines)

    return fallback_line_reference(chunk)


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
        "line_reference": normalize_line_reference(issue.get("line_reference", "file-level"), chunk),
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


def issue_id(index: int) -> str:
    return f"PGX-{index:03d}"


def issue_fingerprint(file_path: str, issue: dict[str, str]) -> tuple[str, str, str, str]:
    normalized_message = " ".join(issue["message"].lower().split())

    return (
        file_path,
        issue["category"],
        issue["line_reference"],
        normalized_message,
    )


def build_canonical_findings(file_reviews: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    finding_ids_by_fingerprint: dict[tuple[str, str, str, str], str] = {}
    files: list[dict[str, Any]] = []

    for file in file_reviews:
        file_path = file["file_path"]
        file_issue_ids = []

        for issue in file["issues"]:
            fingerprint = issue_fingerprint(file_path, issue)
            existing_id = finding_ids_by_fingerprint.get(fingerprint)

            if existing_id:
                if existing_id not in file_issue_ids:
                    file_issue_ids.append(existing_id)
                continue

            new_id = issue_id(len(findings) + 1)
            finding_ids_by_fingerprint[fingerprint] = new_id
            if new_id not in file_issue_ids:
                file_issue_ids.append(new_id)
            findings.append(
                {
                    "id": new_id,
                    "file_path": file_path,
                    "category": issue["category"],
                    "severity": issue["severity"],
                    "line_reference": issue["line_reference"],
                    "message": issue["message"],
                    "suggestion": issue["suggestion"],
                }
            )

        files.append(
            {
                "file_path": file_path,
                "summary": file["summary"],
                "added_lines": file["added_lines"],
                "removed_lines": file["removed_lines"],
                "issue_ids": file_issue_ids,
            }
        )

    return findings, files


def build_issue_index(findings: list[dict[str, str]]) -> dict[str, list[str]]:
    issue_index = {key: [] for key in ISSUE_INDEX_KEYS}

    for finding in findings:
        finding_id = finding["id"]

        if finding["severity"] == "critical":
            issue_index["critical"].append(finding_id)

        category = finding["category"]

        if category == "breaking_change":
            issue_index["breaking_changes"].append(finding_id)
        elif category in issue_index:
            issue_index[category].append(finding_id)

        if finding["suggestion"]:
            issue_index["improvements"].append(finding_id)

    return issue_index


def calculate_risk_from_findings(findings: list[dict[str, str]]) -> str:
    max_rank = 0

    for finding in findings:
        max_rank = max(max_rank, SEVERITY_RANK.get(finding.get("severity", "low"), 1))

    if max_rank >= SEVERITY_RANK["critical"]:
        return "critical"
    if max_rank >= SEVERITY_RANK["high"]:
        return "high"
    if max_rank >= SEVERITY_RANK["medium"]:
        return "medium"
    return "low"


def calculate_recommendation_from_findings(risk_level: str, findings: list[dict[str, str]]) -> str:
    if risk_level in {"high", "critical"}:
        return "REQUEST_CHANGES"

    has_uncertain_review = any(
        finding.get("category") in {"security", "breaking_change", "testing"}
        for finding in findings
    )

    if risk_level == "medium" or has_uncertain_review:
        return "NEEDS_MANUAL_REVIEW"

    return "APPROVE"


def normalize_refined_finding(raw_finding: dict[str, Any], index: int) -> dict[str, str]:
    category = str(raw_finding.get("category", "maintainability")).strip().lower()
    severity = str(raw_finding.get("severity", "medium")).strip().lower()

    if category not in ALLOWED_CATEGORIES:
        category = "maintainability"

    if severity not in ALLOWED_SEVERITIES:
        severity = "medium"

    message = str(raw_finding.get("message") or raw_finding.get("short_message") or "").strip()
    short_message = str(raw_finding.get("short_message") or message).strip()
    suggestion = str(raw_finding.get("suggestion", "")).strip()

    return {
        "id": issue_id(index),
        "source_ids": [
            str(source_id)
            for source_id in raw_finding.get("source_ids", [])
            if source_id
        ],
        "file_path": str(raw_finding.get("file_path", "unknown")).strip() or "unknown",
        "category": category,
        "severity": severity,
        "line_reference": str(raw_finding.get("line_reference", "")).strip(),
        "short_message": short_message,
        "message": message,
        "suggestion": suggestion,
    }


def build_files_from_refined_findings(
    *,
    base_report: dict[str, Any],
    refined_files: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summaries_by_file = {
        str(file.get("file_path", "unknown")): str(file.get("summary", "")).strip()
        for file in refined_files
        if isinstance(file, dict)
    }
    base_files_by_path = {
        str(file.get("file_path", "unknown")): file
        for file in base_report.get("files", [])
        if isinstance(file, dict)
    }
    issue_ids_by_file: dict[str, list[str]] = {}

    for finding in findings:
        file_path = str(finding.get("file_path", "unknown"))
        issue_ids_by_file.setdefault(file_path, []).append(str(finding["id"]))

    ordered_paths = list(base_files_by_path)

    for file_path in issue_ids_by_file:
        if file_path not in ordered_paths:
            ordered_paths.append(file_path)

    files = []

    for file_path in ordered_paths:
        base_file = base_files_by_path.get(file_path, {})
        files.append(
            {
                "file_path": file_path,
                "summary": summaries_by_file.get(file_path) or str(base_file.get("summary", "")),
                "added_lines": int(base_file.get("added_lines", 0)),
                "removed_lines": int(base_file.get("removed_lines", 0)),
                "issue_ids": issue_ids_by_file.get(file_path, []),
            }
        )

    return files


def apply_refined_report(base_report: dict[str, Any], refined_report: dict[str, Any]) -> dict[str, Any]:
    raw_findings = refined_report.get("findings", [])

    if not isinstance(raw_findings, list):
        raw_findings = []

    findings = [
        normalize_refined_finding(raw_finding, index)
        for index, raw_finding in enumerate(raw_findings, start=1)
        if isinstance(raw_finding, dict)
        and str(raw_finding.get("file_path", "")).strip()
        and str(raw_finding.get("message") or raw_finding.get("short_message") or "").strip()
    ]
    refined_files = refined_report.get("files", [])

    if not isinstance(refined_files, list):
        refined_files = []

    files = build_files_from_refined_findings(
        base_report=base_report,
        refined_files=refined_files,
        findings=findings,
    )
    risk_level = calculate_risk_from_findings(findings)
    recommendation = calculate_recommendation_from_findings(risk_level, findings)
    summary = dict(base_report.get("summary", {}))
    summary["risk_level"] = risk_level
    summary["final_recommendation"] = recommendation

    return {
        **base_report,
        "overall_summary": str(
            refined_report.get("overall_summary")
            or base_report.get("overall_summary", "")
        ).strip(),
        "end_summary": str(refined_report.get("end_summary", "")).strip(),
        "summary": summary,
        "files": files,
        "findings": findings,
        "issues": build_issue_index(findings),
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
    findings, files = build_canonical_findings(file_reviews)
    issue_index = build_issue_index(findings)

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
        "files": files,
        "findings": findings,
        "issues": issue_index,
    }
