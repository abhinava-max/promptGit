from promptgitx.ai.chat_graph import (
    classify_git_command_safety,
    git_workflow_execution_node,
    missing_fields_for_git_command,
)


def test_known_read_only_git_command_is_safe():
    safety = classify_git_command_safety(["git", "status"])

    assert safety["is_dangerous"] is False
    assert safety["category"] == "known_safe"


def test_known_mutating_git_command_requires_confirmation():
    result = git_workflow_execution_node({"user_input": "run git reset --hard"})

    assert result["response_type"] == "confirmation"
    assert result["pending_git_workflow_request"]["command"] == ["git", "reset", "--hard"]
    assert "dangerous" in result["response"]


def test_unknown_git_subcommand_is_dangerous_by_default():
    safety = classify_git_command_safety(["git", "worktree", "add", "../copy"])

    assert safety["is_dangerous"] is True
    assert safety["category"] == "unknown"


def test_missing_commit_message_prompts_for_information():
    assert missing_fields_for_git_command(["git", "commit"]) == ["message"]

    result = git_workflow_execution_node({"user_input": "run git commit"})

    assert result["response_type"] == "clarification"
    assert result["pending_git_workflow_request"]["missing"] == ["message"]
    assert "commit message" in result["response"].lower()


def test_confirmation_yes_executes_pending_command(monkeypatch):
    calls = []

    def fake_run_command(command):
        calls.append(command)
        return "done"

    monkeypatch.setattr("promptgitx.gitcodes.command_runner.run_command", fake_run_command)

    result = git_workflow_execution_node(
        {
            "user_input": "yes",
            "pending_git_workflow_request": {
                "command": ["git", "push"],
                "missing": [],
                "awaiting_confirmation": True,
                "safety": {
                    "is_dangerous": True,
                    "category": "known_dangerous",
                    "reason": "`git push` changes remote state.",
                },
            },
        }
    )

    assert calls == [["git", "push"]]
    assert result["pending_git_workflow_request"] is None
    assert result["response_type"] == "command_output"
    assert "done" in result["response"]


def test_confirmation_no_cancels_pending_command():
    result = git_workflow_execution_node(
        {
            "user_input": "no",
            "pending_git_workflow_request": {
                "command": ["git", "push"],
                "missing": [],
                "awaiting_confirmation": True,
            },
        }
    )

    assert result["pending_git_workflow_request"] is None
    assert result["response_type"] == "message"
    assert "cancelled" in result["response"].lower()
