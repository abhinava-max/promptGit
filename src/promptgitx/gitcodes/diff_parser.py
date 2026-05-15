import re
from dataclasses import dataclass, field


@dataclass
class FileDiff:
    file_path: str
    old_file_path: str | None = None
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    changed_lines: list[dict] = field(default_factory=list)
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
    changed_lines: list[dict] = []
    old_line_number: int | None = None
    new_line_number: int | None = None

    for line in file_diff_text.splitlines():
        hunk_match = re.match(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)

        if hunk_match:
            old_line_number = int(hunk_match.group(1))
            new_line_number = int(hunk_match.group(2))
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            content = line[1:]
            added_lines.append(content)

            if new_line_number is not None:
                changed_lines.append(
                    {
                        "kind": "added",
                        "line_number": new_line_number,
                        "reference": f"{file_path}:L{new_line_number}",
                        "content": content,
                    }
                )
                new_line_number += 1

        elif line.startswith("-"):
            content = line[1:]
            removed_lines.append(content)

            if old_line_number is not None:
                changed_lines.append(
                    {
                        "kind": "removed",
                        "line_number": old_line_number,
                        "reference": f"{file_path}:old L{old_line_number}",
                        "content": content,
                    }
                )
                old_line_number += 1

        elif line.startswith(" "):
            if old_line_number is not None:
                old_line_number += 1
            if new_line_number is not None:
                new_line_number += 1

    return FileDiff(
        file_path=file_path,
        old_file_path=old_file_path,
        added_lines=added_lines,
        removed_lines=removed_lines,
        changed_lines=changed_lines,
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
            "parent_file_path": file.file_path,
            "added_lines_count": len(file.added_lines),
            "removed_lines_count": len(file.removed_lines),
            "parent_added_lines_count": len(file.added_lines),
            "parent_removed_lines_count": len(file.removed_lines),
            "changed_lines": file.changed_lines,
            "chunk_part": 1,
            "chunk_total": 1,
            "was_split": False,
            "raw_diff": file.raw_diff,
        })

    return chunks


def split_file_diff_by_hunks(raw_diff: str) -> tuple[str, list[str]]:
    hunk_matches = list(re.finditer(r"^@@ .*$", raw_diff, flags=re.MULTILINE))

    if not hunk_matches:
        return raw_diff, []

    header = raw_diff[:hunk_matches[0].start()].strip()
    hunks = []

    for index, match in enumerate(hunk_matches):
        start = match.start()
        end = hunk_matches[index + 1].start() if index + 1 < len(hunk_matches) else len(raw_diff)
        hunks.append(raw_diff[start:end].strip())

    return header, hunks


def build_review_subchunk(parent_chunk: dict, raw_diff: str, part: int, total: int) -> dict:
    parsed = parse_file_diff(raw_diff)

    return {
        **parent_chunk,
        "added_lines_count": len(parsed.added_lines) if parsed else 0,
        "removed_lines_count": len(parsed.removed_lines) if parsed else 0,
        "changed_lines": parsed.changed_lines if parsed else [],
        "chunk_part": part,
        "chunk_total": total,
        "was_split": total > 1,
        "raw_diff": raw_diff,
    }


def split_large_diff_chunks(chunks: list[dict], max_chars: int = 12000) -> list[dict]:
    """
    Splits oversized file diffs into hunk-based subchunks without dropping diff data.
    """

    split_chunks = []

    for chunk in chunks:
        raw_diff = chunk["raw_diff"]

        if len(raw_diff) <= max_chars:
            split_chunks.append({
                **chunk,
                "chunk_part": 1,
                "chunk_total": 1,
                "was_split": False,
                "was_trimmed": False,
            })
            continue

        header, hunks = split_file_diff_by_hunks(raw_diff)

        if not hunks:
            split_chunks.append({
                **chunk,
                "chunk_part": 1,
                "chunk_total": 1,
                "was_split": False,
                "was_trimmed": False,
            })
            continue

        grouped_hunks: list[list[str]] = []
        current_group: list[str] = []

        for hunk in hunks:
            candidate_group = current_group + [hunk]
            candidate_raw_diff = "\n".join([header, *candidate_group]).strip()

            if current_group and len(candidate_raw_diff) > max_chars:
                grouped_hunks.append(current_group)
                current_group = [hunk]
            else:
                current_group = candidate_group

        if current_group:
            grouped_hunks.append(current_group)

        total = len(grouped_hunks)

        for index, group in enumerate(grouped_hunks, start=1):
            subchunk_raw_diff = "\n".join([header, *group]).strip()
            split_chunks.append(build_review_subchunk(chunk, subchunk_raw_diff, index, total))

    return split_chunks


def filter_large_diff_chunks(chunks: list[dict], max_chars: int = 12000) -> list[dict]:
    """
    Backward-compatible alias. Large diffs are now split instead of trimmed.
    """

    return split_large_diff_chunks(chunks, max_chars=max_chars)
