from typing import Optional

from .command_runner import run_command
from .git_info import ensure_git_repo, ensure_gh_available


DEFAULT_CONTEXT_LINES = 80


def get_commit_diff(commit_hash: str, context_lines: int = DEFAULT_CONTEXT_LINES) -> str:
    """
    Gets diff for a single commit.

    Example:
        git show --format= --unified=80 abc123

    Meaning:
        Show only code changes of commit abc123 with 80 lines of context.
    """

    ensure_git_repo()

    if not commit_hash:
        raise ValueError("commit_hash is required")

    return run_command([
        "git",
        "show",
        "--format=",
        f"--unified={context_lines}",
        commit_hash,
    ])


def get_multiple_commits_diff(
    commits: list[str],
    context_lines: int = DEFAULT_CONTEXT_LINES,
) -> str:
    """
    Gets diffs for multiple commits and combines them.

    Example:
        commits = ["abc123", "def456"]
    """

    ensure_git_repo()

    if not commits:
        raise ValueError("At least one commit hash is required")

    all_diffs = []

    for commit_hash in commits:
        diff = get_commit_diff(commit_hash, context_lines=context_lines)

        section = f"""
==============================
COMMIT: {commit_hash}
==============================

{diff}
"""
        all_diffs.append(section)

    return "\n\n".join(all_diffs)


def get_last_commit_diff(context_lines: int = DEFAULT_CONTEXT_LINES) -> str:
    """
    Gets diff for latest commit.

    Same as:
        git show --format= --unified=80 HEAD
    """

    ensure_git_repo()

    return get_commit_diff("HEAD", context_lines=context_lines)


def get_last_n_commits_diff(
    n: int,
    context_lines: int = DEFAULT_CONTEXT_LINES,
) -> str:
    """
    Gets combined diff for last n commits.

    Example:
        gitpromptx review --last-n 3

    Internally:
        git diff HEAD~3..HEAD
    """

    ensure_git_repo()

    if n <= 0:
        raise ValueError("n must be greater than 0")

    return run_command([
        "git",
        "diff",
        f"HEAD~{n}..HEAD",
        f"--unified={context_lines}",
    ])


def get_staged_diff(context_lines: int = DEFAULT_CONTEXT_LINES) -> str:
    """
    Gets diff for staged changes.

    Staged means files already added using:
        git add .

    Internally:
        git diff --cached
    """

    ensure_git_repo()

    return run_command([
        "git",
        "diff",
        "--cached",
        f"--unified={context_lines}",
    ])


def get_unstaged_diff(context_lines: int = DEFAULT_CONTEXT_LINES) -> str:
    """
    Gets diff for unstaged changes.

    Unstaged means files modified but not added using git add.
    """

    ensure_git_repo()

    return run_command([
        "git",
        "diff",
        f"--unified={context_lines}",
    ])


def get_compare_diff(
    compare_text: str,
    context_lines: int = DEFAULT_CONTEXT_LINES,
    use_triple_dot: bool = False,
) -> str:
    """
    Gets diff between any two Git refs.

    Examples:
        main..feature-login
        abc123..def456
        HEAD~3..HEAD

    Two-dot:
        main..feature-login

    Triple-dot:
        main...feature-login

    For simple MVP, two-dot is okay.
    For PR-style branch review, triple-dot can be better.
    """

    ensure_git_repo()

    if not compare_text:
        raise ValueError("compare_text is required")

    if ".." not in compare_text:
        raise ValueError("Compare value must look like: main..feature-login")

    left, right = compare_text.split("..", 1)

    if not left or not right:
        raise ValueError("Compare value must have both sides. Example: main..feature-login")

    diff_range = f"{left}...{right}" if use_triple_dot else f"{left}..{right}"

    return run_command([
        "git",
        "diff",
        diff_range,
        f"--unified={context_lines}",
    ])


def get_branch_diff(
    branch: str,
    base: str = "main",
    context_lines: int = DEFAULT_CONTEXT_LINES,
) -> str:
    """
    Gets diff of a branch compared to base branch.

    Example:
        branch = feature-login
        base = main

    Internally:
        git diff main...feature-login --unified=80
    """

    ensure_git_repo()

    if not branch:
        raise ValueError("branch is required")

    if not base:
        raise ValueError("base branch is required")

    return run_command([
        "git",
        "diff",
        f"{base}...{branch}",
        f"--unified={context_lines}",
    ])


def get_file_diff(
    file_path: str,
    compare_text: Optional[str] = None,
    context_lines: int = DEFAULT_CONTEXT_LINES,
) -> str:
    """
    Gets diff for a specific file.

    If compare_text is given:
        git diff main..feature -- file.py

    Else:
        git diff -- file.py
    """

    ensure_git_repo()

    if not file_path:
        raise ValueError("file_path is required")

    command = ["git", "diff"]

    if compare_text:
        command.append(compare_text)

    command.extend([
        f"--unified={context_lines}",
        "--",
        file_path,
    ])

    return run_command(command)


def get_pr_diff(pr_number: int) -> str:
    """
    Gets Pull Request diff using GitHub CLI.

    Internally:
        gh pr diff 24
    """

    ensure_git_repo()
    ensure_gh_available()

    if pr_number <= 0:
        raise ValueError("PR number must be greater than 0")

    return run_command([
        "gh",
        "pr",
        "diff",
        str(pr_number),
    ])


def get_pr_metadata(pr_number: int) -> str:
    """
    Gets PR metadata like title, author, base branch, head branch.

    Internally:
        gh pr view 24
    """

    ensure_git_repo()
    ensure_gh_available()

    if pr_number <= 0:
        raise ValueError("PR number must be greater than 0")

    return run_command([
        "gh",
        "pr",
        "view",
        str(pr_number),
    ])
