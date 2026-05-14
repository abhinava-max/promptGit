import re
from dataclasses import dataclass, field


@dataclass
class FileDiff:
    file_path: str
    old_file_path: str | None = None
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    raw_diff: str = ""


@dataclass
class ParsedDiff:
    files: list[FileDiff]
    total_files: int
    total_added_lines: int
    total_removed_lines: int


def parse_diff(diff_text: str) -> ParsedDiff:
    """
    Parses a git diff into file-level data.

    Extracts:
        - file path
        - added lines
        - removed lines
        - raw diff per file
    """

    if not diff_text.strip():
        return ParsedDiff(
            files=[],
            total_files=0,
            total_added_lines=0,
            total_removed_lines=0,
        )

    file_sections = split_diff_by_file(diff_text)
    parsed_files: list[FileDiff] = []

    for section in file_sections:
        file_diff = parse_file_diff(section)

        if file_diff:
            parsed_files.append(file_diff)

    total_added = sum(len(file.added_lines) for file in parsed_files)
    total_removed = sum(len(file.removed_lines) for file in parsed_files)

    return ParsedDiff(
        files=parsed_files,
        total_files=len(parsed_files),
        total_added_lines=total_added,
        total_removed_lines=total_removed,
    )


def split_diff_by_file(diff_text: str) -> list[str]:
    """
    Splits full diff into individual file diffs.
    """

    sections = re.split(r"(?=^diff --git )", diff_text, flags=re.MULTILINE)

    return [
        section.strip()
        for section in sections
        if section.strip().startswith("diff --git")
    ]


def parse_file_diff(file_diff_text: str) -> FileDiff | None:
    """
    Parses one file diff section.
    """

    file_path = extract_file_path(file_diff_text)
    old_file_path = extract_old_file_path(file_diff_text)

    if not file_path:
        return None

    added_lines: list[str] = []
    removed_lines: list[str] = []

    for line in file_diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            added_lines.append(line[1:])

        elif line.startswith("-"):
            removed_lines.append(line[1:])

    return FileDiff(
        file_path=file_path,
        old_file_path=old_file_path,
        added_lines=added_lines,
        removed_lines=removed_lines,
        raw_diff=file_diff_text,
    )


def extract_file_path(file_diff_text: str) -> str | None:
    """
    Extracts new file path from diff.

    Example:
        diff --git a/main.py b/main.py
        returns main.py
    """

    first_line = file_diff_text.splitlines()[0] if file_diff_text.splitlines() else ""

    match = re.match(r"diff --git a/(.*?) b/(.*)", first_line)

    if match:
        return match.group(2).strip()

    return None


def extract_old_file_path(file_diff_text: str) -> str | None:
    """
    Extracts old file path from diff.
    """

    first_line = file_diff_text.splitlines()[0] if file_diff_text.splitlines() else ""

    match = re.match(r"diff --git a/(.*?) b/(.*)", first_line)

    if match:
        return match.group(1).strip()

    return None


def get_changed_file_paths(diff_text: str) -> list[str]:
    """
    Returns only changed file paths from diff.
    """

    parsed = parse_diff(diff_text)

    return [file.file_path for file in parsed.files]


def summarize_diff(diff_text: str) -> dict:
    """
    Returns simple summary of diff.
    """

    parsed = parse_diff(diff_text)

    return {
        "total_files": parsed.total_files,
        "total_added_lines": parsed.total_added_lines,
        "total_removed_lines": parsed.total_removed_lines,
        "files": [
            {
                "file_path": file.file_path,
                "added_lines": len(file.added_lines),
                "removed_lines": len(file.removed_lines),
            }
            for file in parsed.files
        ],
    }


def chunk_diff_by_file(diff_text: str) -> list[dict]:
    """
    Converts diff into chunks per file.

    Useful before sending to AI.
    """

    parsed = parse_diff(diff_text)

    chunks = []

    for file in parsed.files:
        chunks.append({
            "file_path": file.file_path,
            "added_lines_count": len(file.added_lines),
            "removed_lines_count": len(file.removed_lines),
            "raw_diff": file.raw_diff,
        })

    return chunks


def filter_large_diff_chunks(
    chunks: list[dict],
    max_chars: int = 12000,
) -> list[dict]:
    """
    Trims very large file diffs so they don't exceed LLM context too much.
    """

    filtered_chunks = []

    for chunk in chunks:
        raw_diff = chunk["raw_diff"]

        if len(raw_diff) > max_chars:
            chunk = {
                **chunk,
                "raw_diff": raw_diff[:max_chars],
                "was_trimmed": True,
            }
        else:
            chunk = {
                **chunk,
                "was_trimmed": False,
            }

        filtered_chunks.append(chunk)

    return filtered_chunks