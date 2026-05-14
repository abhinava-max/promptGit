from .command_runner import run_command, command_exists


def ensure_git_available() -> None:
    """
    Ensures git is installed.
    """

    if not command_exists("git"):
        raise RuntimeError("Git is not installed or not available in PATH.")


def ensure_gh_available() -> None:
    """
    Ensures GitHub CLI is installed.
    """

    if not command_exists("gh"):
        raise RuntimeError("GitHub CLI 'gh' is not installed or not available in PATH.")


def is_git_repo() -> bool:
    """
    Checks if current folder is inside a Git repository.
    """

    try:
        output = run_command(["git", "rev-parse", "--is-inside-work-tree"])
        return output == "true"

    except RuntimeError:
        return False


def ensure_git_repo() -> None:
    """
    Raises error if current folder is not a Git repository.
    """

    ensure_git_available()

    if not is_git_repo():
        raise RuntimeError("This folder is not a Git repository.")


def get_current_branch() -> str:
    """
    Returns current branch name.
    """

    ensure_git_repo()
    return run_command(["git", "branch", "--show-current"])


def get_repo_root() -> str:
    """
    Returns root path of the Git repository.
    """

    ensure_git_repo()
    return run_command(["git", "rev-parse", "--show-toplevel"])


def get_remote_url(remote_name: str = "origin") -> str:
    """
    Returns remote URL.
    """

    ensure_git_repo()
    return run_command(["git", "remote", "get-url", remote_name])


def get_latest_commit_hash() -> str:
    """
    Returns latest commit hash.
    """

    ensure_git_repo()
    return run_command(["git", "rev-parse", "HEAD"])


def get_last_n_commit_hashes(n: int) -> list[str]:
    """
    Returns last n commit hashes.
    """

    ensure_git_repo()

    if n <= 0:
        raise ValueError("n must be greater than 0")

    output = run_command(["git", "log", f"-{n}", "--pretty=format:%H"])

    if not output:
        return []

    return output.splitlines()


def validate_git_ref(ref: str) -> bool:
    """
    Checks if a commit/branch/tag/ref exists.
    """

    ensure_git_repo()

    try:
        run_command(["git", "rev-parse", "--verify", ref])
        return True

    except RuntimeError:
        return False


def get_changed_files_from_commit(commit_hash: str) -> list[str]:
    """
    Returns changed files in a commit.
    """

    ensure_git_repo()

    output = run_command([
        "git",
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit_hash,
    ])

    if not output:
        return []

    return output.splitlines()


def get_changed_files_from_compare(compare_text: str) -> list[str]:
    """
    Returns changed files between two refs.

    Example:
        main..feature-login
        abc123..def456
        HEAD~3..HEAD
    """

    ensure_git_repo()

    if ".." not in compare_text:
        raise ValueError("Compare value must look like: main..feature-login")

    output = run_command([
        "git",
        "diff",
        "--name-only",
        compare_text,
    ])

    if not output:
        return []

    return output.splitlines()


def get_changed_files_from_staged() -> list[str]:
    """
    Returns staged changed files.
    """

    ensure_git_repo()

    output = run_command([
        "git",
        "diff",
        "--cached",
        "--name-only",
    ])

    if not output:
        return []

    return output.splitlines()
