import re
import shlex

from langgraph.graph import StateGraph, END, START
from .graph_state import ChatGraphState

from .llm_provider import RuntimeModelRouter
from .json_utils import extract_json_object, to_pretty_json
from langchain_core.output_parsers import StrOutputParser

from ..prompts import (
    get_chat_intent_prompt,
    get_git_github_question_prompt,
    get_git_workflow_request_extractor_prompt,
    get_promptgitx_help_prompt,
    get_report_request_extractor_prompt,
)

ALLOWED_CHAT_INTENTS = {
    "git_workflow_execution",
    "git_github_question",
    "promptgitx_query",
    "promptgitx_report_generation",
    "out_of_scope",
}

REPORT_TARGET_RE = re.compile(
    r"\b("
    r"pr|pull\s+request|staged|changes?|diff|commits?|last\s+\d+|last|"
    r"report|review|analysis"
    r")\b",
    re.IGNORECASE,
)
PR_ORDINAL_RE = re.compile(
    r"\b("
    r"\d+(?:st|nd|rd|th)|first|second|third|fourth|fifth|sixth|seventh|"
    r"eighth|ninth|tenth"
    r")\s+(?:pr|pull\s+request)\b",
    re.IGNORECASE,
)
COMPARE_RANGE_RE = re.compile(r"\S+\.\.\.?\S+")
HELP_QUESTION_RE = re.compile(r"^\s*(how|what|where|when|why)\b", re.IGNORECASE)
CAPABILITY_QUESTION_RE = re.compile(
    r"^\s*(can|could|should)\s+(promptgitx|it|this\s+tool|the\s+cli)\b",
    re.IGNORECASE,
)
GIT_EXAMPLE_REQUEST_RE = re.compile(
    r"\b("
    r"how\s+(?:do|to)|what\s+is|what\s+does|explain|show\s+me|give\s+me|"
    r"single\s+line|one\s+line|example|syntax|command\s+for|code\s+for"
    r")\b.*\b(git|gh|rebase|merge|checkout|switch|reset|push|pull|commit|stash|branch|tag)\b",
    re.IGNORECASE,
)
EXECUTION_REQUEST_RE = re.compile(
    r"^\s*(?:please\s+)?(?:can|could|would)?\s*(?:you\s+)?"
    r"(run|execute|do|perform|apply|start)\b|\bfor\s+me\b",
    re.IGNORECASE,
)
DIRECT_REPORT_ACTION_RE = re.compile(
    r"^\s*(?:please\s+)?(?:can|could|would)?\s*(?:you\s+)?"
    r"(analy[sz]e|review|compare|create|generate|make|check|scan|inspect)\b",
    re.IGNORECASE,
)
BRANCH_PAIR_RE = re.compile(
    r"\bcompare\s+([A-Za-z0-9._/-]+)\s+(?:to|with|and|against)\s+([A-Za-z0-9._/-]+)\b",
    re.IGNORECASE,
)
BRANCH_COMPARE_RE = re.compile(r"\b(analy[sz]e|review|compare)\b.*\bbranch(?:es)?\b", re.IGNORECASE)
REPORT_MODES = {"staged", "last", "last_n", "commit", "commits", "compare", "pr"}
GIT_WORKFLOW_EXECUTABLES = {"git", "gh"}
CONFIRMATION_YES_RE = re.compile(r"^\s*(y|yes|yeah|yep|continue|proceed|run it|execute it|do it)\s*[.!]?\s*$", re.IGNORECASE)
CONFIRMATION_NO_RE = re.compile(r"^\s*(n|no|nope|don't|do not|cancel|stop|nevermind|never mind)\s*[.!]?\s*$", re.IGNORECASE)
CHANGE_COMMAND_RE = re.compile(r"\b(change|edit|modify|instead|different|use this|make it)\b", re.IGNORECASE)

SAFE_GIT_SUBCOMMANDS = {
    "status",
    "log",
    "show",
    "diff",
    "rev-parse",
    "ls-files",
}
SAFE_GIT_NESTED_SUBCOMMANDS = {
    "branch": {None, "-a", "--all", "-r", "--remotes", "--show-current", "--list"},
    "remote": {None, "-v", "--verbose", "get-url", "show"},
}
SAFE_GH_SUBCOMMANDS = {
    "auth",
    "status",
    "pr",
    "repo",
    "issue",
    "api",
}
SAFE_GH_NESTED_SUBCOMMANDS = {
    "pr": {"list", "view", "status", "checks", "diff"},
    "repo": {"view", "list"},
    "issue": {"list", "view", "status"},
}
DANGEROUS_GIT_SUBCOMMANDS = {
    "add",
    "am",
    "apply",
    "bisect",
    "checkout",
    "cherry-pick",
    "clean",
    "clone",
    "commit",
    "fetch",
    "merge",
    "mv",
    "pull",
    "push",
    "rebase",
    "reset",
    "restore",
    "revert",
    "rm",
    "stash",
    "submodule",
    "switch",
    "tag",
}


def is_direct_report_generation_request(user_input: str) -> bool:
    text = user_input.strip().lower()

    if not text:
        return False

    if HELP_QUESTION_RE.search(text) or CAPABILITY_QUESTION_RE.search(text):
        return False

    has_direct_report_action = DIRECT_REPORT_ACTION_RE.search(text) is not None
    has_report_target = REPORT_TARGET_RE.search(text) is not None
    has_pr_ordinal = PR_ORDINAL_RE.search(text) is not None
    has_compare_range = COMPARE_RANGE_RE.search(text) is not None
    has_branch_compare = BRANCH_COMPARE_RE.search(text) is not None
    has_branch_pair = BRANCH_PAIR_RE.search(text) is not None

    return has_direct_report_action and (
        has_report_target
        or has_pr_ordinal
        or has_compare_range
        or has_branch_compare
        or has_branch_pair
    )

def maybe_correct_chat_intent(intent: str, user_input: str) -> tuple[str, str | None]:
    if intent == "git_workflow_execution" and GIT_EXAMPLE_REQUEST_RE.search(user_input):
        if not EXECUTION_REQUEST_RE.search(user_input):
            return (
                "git_github_question",
                "Corrected an example-style Git question after LLM classification.",
            )

    if intent != "promptgitx_report_generation" and is_direct_report_generation_request(user_input):
        return (
            "promptgitx_report_generation",
            "Corrected an action-style report request after LLM classification.",
        )

    return intent, None

def missing_fields_for_request(request: dict) -> list[str]:
    mode = request.get("mode")

    if not mode:
        return ["target"]

    required_fields = {
        "pr": ["pr"],
        "commit": ["commit"],
        "commits": ["commits"],
        "compare": ["compare"],
        "last_n": ["last_n"],
    }

    return [
        field
        for field in required_fields.get(mode, [])
        if not request.get(field)
    ]

def clarification_for_request(request: dict) -> str:
    missing = set(request.get("missing") or missing_fields_for_request(request))
    mode = request.get("mode")

    if "target" in missing:
        return (
            "What should I review? You can say something like `PR 2`, "
            "`staged changes`, `last commit`, `last 3 commits`, or `main..feature`."
        )

    if mode == "pr" and "pr" in missing:
        return "Which PR number should I review?"

    if mode == "compare" and "compare" in missing:
        return "Which refs should I compare? Use a range like `main..feature`."

    if mode == "commit" and "commit" in missing:
        return "Which commit should I review? Send a commit SHA or revision."

    if mode == "commits" and "commits" in missing:
        return "Which commits should I review? Send the commit SHAs separated by spaces."

    if mode == "last_n" and "last_n" in missing:
        return "How many recent commits should I review?"

    return "I need one more detail before I can generate the report."

def normalize_report_request(raw_request: dict) -> dict:
    request = dict(raw_request)
    mode = request.get("mode")

    if mode == "null":
        mode = None

    if mode not in REPORT_MODES:
        mode = None

    request["mode"] = mode

    if mode == "pr" and request.get("pr") is not None:
        try:
            request["pr"] = int(request["pr"])
        except (TypeError, ValueError):
            request["pr"] = None

    if mode == "last_n" and request.get("last_n") is not None:
        try:
            request["last_n"] = int(request["last_n"])
        except (TypeError, ValueError):
            request["last_n"] = None

    if mode == "staged":
        request["staged"] = True

    if mode == "last":
        request["last"] = True

    if mode == "commits" and isinstance(request.get("commits"), str):
        request["commits"] = [
            commit
            for commit in request["commits"].replace(",", " ").split()
            if commit
        ]

    request["missing"] = missing_fields_for_request(request)

    if request.get("missing") and not request.get("clarification_question"):
        request["clarification_question"] = clarification_for_request(request)

    return request

def extract_report_request(user_input: str, pending: dict | None = None) -> dict:
    prompt = get_report_request_extractor_prompt()
    pending_json = to_pretty_json(pending or {})
    raw = invoke_with_model_fallback(
        prompt,
        {
            "user_input": user_input,
            "pending_report_request": pending_json,
        },
    )

    try:
        request = extract_json_object(raw)
    except Exception:
        request = {
            "mode": None,
            "missing": ["target"],
            "clarification_question": clarification_for_request({"mode": None}),
        }

    return normalize_report_request(request)

def normalize_git_workflow_request(raw_request: dict, pending: dict | None = None) -> dict:
    request = dict(raw_request)
    pending = pending or {}

    if request.get("approved") is None and CONFIRMATION_YES_RE.match(str(request.get("user_input", ""))):
        request["approved"] = True

    command = request.get("command")
    if command is None and pending and not request.get("change_requested"):
        command = pending.get("command")

    if isinstance(command, str):
        try:
            command = shlex.split(command)
        except ValueError:
            command = None

    if not isinstance(command, list) or not all(isinstance(token, str) for token in command):
        command = None

    if command is not None:
        command = [token for token in command if token]

    request["command"] = command
    request["missing"] = request.get("missing") or []

    if request.get("cancelled"):
        request["approved"] = False

    if command and not request.get("missing"):
        request["missing"] = missing_fields_for_git_command(command)

    if request["missing"] and not request.get("clarification_question"):
        request["clarification_question"] = clarification_for_git_workflow_request(request)

    return request

def extract_direct_git_command(user_input: str) -> list[str] | None:
    text = user_input.strip()

    if not text:
        return None

    lowered = text.lower()
    for prefix in ("run ", "execute "):
        if lowered.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    if not re.match(r"^(git|gh)(\s|$)", text):
        return None

    try:
        command = shlex.split(text)
    except ValueError:
        return None

    return command or None

def extract_git_workflow_request(user_input: str, pending: dict | None = None) -> dict:
    if pending and CONFIRMATION_YES_RE.match(user_input):
        return normalize_git_workflow_request(
            {"approved": True, "command": pending.get("command"), "missing": []},
            pending,
        )

    if pending and CONFIRMATION_NO_RE.match(user_input):
        return normalize_git_workflow_request(
            {"approved": False, "cancelled": True, "command": pending.get("command"), "missing": []},
            pending,
        )

    direct_command = extract_direct_git_command(user_input)
    if direct_command and not (pending and CHANGE_COMMAND_RE.search(user_input)):
        return normalize_git_workflow_request(
            {
                "cancelled": False,
                "approved": None,
                "change_requested": False,
                "command": direct_command,
                "missing": [],
                "clarification_question": None,
            },
            pending,
        )

    prompt = get_git_workflow_request_extractor_prompt()
    pending_json = to_pretty_json(pending or {})
    raw = invoke_with_model_fallback(
        prompt,
        {
            "user_input": user_input,
            "pending_git_workflow_request": pending_json,
        },
    )

    try:
        request = extract_json_object(raw)
    except Exception:
        request = {
            "command": None,
            "missing": ["command"],
            "clarification_question": "Which git or gh command should I run?",
        }

    request["user_input"] = user_input
    return normalize_git_workflow_request(request, pending)

def missing_fields_for_git_command(command: list[str]) -> list[str]:
    if len(command) < 2:
        return ["command"]

    executable, subcommand = command[0], command[1]
    args = command[2:]

    if executable not in GIT_WORKFLOW_EXECUTABLES:
        return ["command"]

    if executable == "git":
        if subcommand in {"checkout", "switch", "merge", "rebase", "reset", "revert", "cherry-pick"} and not args:
            return ["target"]

        if subcommand == "commit":
            has_message = any(arg == "-m" or arg.startswith("-m") or arg == "--message" for arg in args)
            if not has_message:
                return ["message"]

        if subcommand == "branch":
            mutating_flags = {"-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy"}
            if any(arg in mutating_flags for arg in args) and len([arg for arg in args if not arg.startswith("-")]) == 0:
                return ["target"]

    if executable == "gh":
        if subcommand == "pr" and len(args) >= 1 and args[0] in {"checkout", "merge", "close", "reopen", "ready", "lock", "unlock"} and len(args) == 1:
            return ["target"]

        if subcommand in {"repo", "issue", "release"} and len(args) >= 1 and args[0] in {"create", "delete", "edit", "close", "reopen"} and len(args) == 1:
            return ["target"]

    return []

def clarification_for_git_workflow_request(request: dict) -> str:
    missing = set(request.get("missing") or [])
    command = request.get("command") or []

    if "command" in missing:
        return "Which git or gh command should I run?"

    if "message" in missing:
        return "What commit message should I use?"

    if "target" in missing:
        rendered = render_command(command) if command else "that command"
        return f"What target should I use for `{rendered}`?"

    return "I need one more detail before I can run that Git workflow command."

def render_command(command: list[str]) -> str:
    return " ".join(shlex.quote(token) for token in command)

def classify_git_command_safety(command: list[str]) -> dict:
    if not command:
        return {
            "is_dangerous": True,
            "reason": "No command was provided.",
            "category": "unknown",
        }

    executable = command[0]
    if executable not in GIT_WORKFLOW_EXECUTABLES:
        return {
            "is_dangerous": True,
            "reason": "Only git and gh commands are supported here.",
            "category": "unknown",
        }

    if len(command) == 1:
        return {
            "is_dangerous": False,
            "reason": "This only prints top-level command help.",
            "category": "known_safe",
        }

    subcommand = command[1]

    if executable == "git":
        if subcommand in DANGEROUS_GIT_SUBCOMMANDS:
            return {
                "is_dangerous": True,
                "reason": f"`git {subcommand}` can change repository or remote state.",
                "category": "known_dangerous",
            }

        if subcommand == "branch":
            mutating_flags = {"-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy"}
            if any(arg in mutating_flags for arg in command[2:]):
                return {
                    "is_dangerous": True,
                    "reason": "`git branch` with mutating flags can change branch state.",
                    "category": "known_dangerous",
                }
            nested = command[2] if len(command) > 2 else None
            if nested in SAFE_GIT_NESTED_SUBCOMMANDS["branch"]:
                return {
                    "is_dangerous": False,
                    "reason": "`git branch` is treated as read-only for listing/current-branch usage.",
                    "category": "known_safe",
                }
            return {
                "is_dangerous": True,
                "reason": "`git branch` with a branch name can create or change branch state.",
                "category": "known_dangerous",
            }

        if subcommand == "remote":
            nested = command[2] if len(command) > 2 else None
            if nested in SAFE_GIT_NESTED_SUBCOMMANDS["remote"]:
                return {
                    "is_dangerous": False,
                    "reason": "`git remote` is treated as read-only for listing/show/get-url usage.",
                    "category": "known_safe",
                }
            return {
                "is_dangerous": True,
                "reason": "`git remote` can change remote configuration with some subcommands.",
                "category": "known_dangerous",
            }

        if subcommand in SAFE_GIT_SUBCOMMANDS:
            return {
                "is_dangerous": False,
                "reason": f"`git {subcommand}` is treated as read-only.",
                "category": "known_safe",
            }

    if executable == "gh":
        nested = command[2] if len(command) > 2 else None

        if subcommand in SAFE_GH_NESTED_SUBCOMMANDS and nested in SAFE_GH_NESTED_SUBCOMMANDS[subcommand]:
            return {
                "is_dangerous": False,
                "reason": f"`gh {subcommand} {nested}` is treated as read-only.",
                "category": "known_safe",
            }

        if subcommand in SAFE_GH_SUBCOMMANDS and nested is None:
            return {
                "is_dangerous": False,
                "reason": f"`gh {subcommand}` is treated as read-only.",
                "category": "known_safe",
            }

    return {
        "is_dangerous": True,
        "reason": "This command is not in the known safe command list, so it is treated as dangerous/unknown.",
        "category": "unknown",
    }

def confirmation_for_git_command(command: list[str], safety: dict) -> str:
    category = safety.get("category", "unknown")
    label = "dangerous" if category != "unknown" else "dangerous/unknown"
    return (
        f"I can run `{render_command(command)}`, but it is classified as {label}.\n\n"
        f"Reason: {safety.get('reason')}\n\n"
        "Reply `yes` to run it, `no` to cancel, or send a changed command."
    )

def invoke_with_model_fallback(prompt, prompt_input: dict) -> str:
    model_router = RuntimeModelRouter()
    last_error: Exception | None = None

    try:
        chain = prompt | model_router.create_current_chat_model() | StrOutputParser()
        return chain.invoke(prompt_input)
    except Exception as error:
        last_error = error
        while model_router.has_next_model():
            model_router.advance_model()
            chain = prompt | model_router.create_current_chat_model() | StrOutputParser()
            try:
                return chain.invoke(prompt_input)
            except Exception as retry_error:
                last_error = retry_error

    if last_error is not None:
        raise last_error

    raise RuntimeError("No LLM response was generated.")

def classify_chat_intent_node(state: ChatGraphState) -> ChatGraphState:
    user_input = state.get("user_input", "")

    if state.get("pending_git_workflow_request") is not None:
        return {
            "intent": "git_workflow_execution",
            "intent_reason": "Continuing a pending Git workflow request.",
        }

    if state.get("pending_report_request") is not None:
        return {
            "intent": "promptgitx_report_generation",
            "intent_reason": "Continuing a pending report request.",
        }

    prompt = get_chat_intent_prompt()
    raw = invoke_with_model_fallback(prompt, {"user_input": user_input})

    try:
        parsed = extract_json_object(raw)
    except Exception as e:
        parsed = {
            "intent": "out_of_scope",
            "intent_reason": "Failed to parse intent from LLM response",
        }
    intent = str(parsed.get("intent", "out_of_scope")).strip().lower()

    if intent not in ALLOWED_CHAT_INTENTS:
        intent = "out_of_scope"

    intent_reason = str(parsed.get("reason", "")).strip()
    intent, correction_reason = maybe_correct_chat_intent(intent, user_input)

    return {"intent": intent,
            "intent_reason": correction_reason or intent_reason,
    }

def git_github_question_node(state: ChatGraphState) -> ChatGraphState:
    prompt = get_git_github_question_prompt()

    response = invoke_with_model_fallback(
        prompt,
        {
            "user_input": state.get("user_input", ""),
            "intent_reason": state.get("intent_reason", ""),
        },
    )

    return {"response": response.strip()}

def promptgitx_query_node(state: ChatGraphState) -> ChatGraphState:
    prompt = get_promptgitx_help_prompt()
    help_context = state.get("help_context", "")

    if not help_context:
        app = state.get("promptgitx_app")

        if app is None:
            return {
                "response": "PromptGitX help is unavailable right now because the CLI app context was not provided."
            }

        from .chat_agent import collect_promptgitx_help

        help_context = collect_promptgitx_help(app)

    response = invoke_with_model_fallback(
        prompt,
        {
            "user_input": state.get("user_input", ""),
            "help_context": help_context,
        },
    )

    return {
        "help_context": help_context,
        "response": response.strip(),
    }
def promptgitx_report_generation_node(state: ChatGraphState) -> ChatGraphState:
    if state.get("pending_report_request") is None:
        user_input = state.get("user_input", "")

        if HELP_QUESTION_RE.search(user_input) or CAPABILITY_QUESTION_RE.search(user_input):
            return promptgitx_query_node(state)

    request = extract_report_request(
        state.get("user_input", ""),
        state.get("pending_report_request"),
    )

    if request.get("cancelled"):
        return {
            "pending_report_request": None,
            "response_type": "message",
            "response": "Okay, I cancelled the pending report request.",
        }

    if request.get("missing"):
        return {
            "pending_report_request": request,
            "report_request": request,
            "response_type": "clarification",
            "response": request.get("clarification_question") or clarification_for_request(request),
        }

    try:
        from .pr_analyzer import create_report

        report = create_report(
            mode=request["mode"],
            commit=request.get("commit"),
            commits=request.get("commits"),
            compare=request.get("compare"),
            pr=request.get("pr"),
            last=request.get("last"),
            last_n=request.get("last_n"),
            staged=request.get("staged"),
        )
    except Exception as error:
        return {
            "pending_report_request": None,
            "report_request": request,
            "response_type": "error",
            "response": f"Failed to generate review report: {error}",
        }

    if not report:
        return {
            "pending_report_request": None,
            "report_request": request,
            "response_type": "error",
            "response": "No report was generated.",
        }

    return {
        "pending_report_request": None,
        "report_request": request,
        "response_type": "report",
        "report": report,
    }

def git_workflow_execution_node(state: ChatGraphState) -> ChatGraphState:
    request = extract_git_workflow_request(
        state.get("user_input", ""),
        state.get("pending_git_workflow_request"),
    )

    if request.get("cancelled") or request.get("approved") is False:
        return {
            "pending_git_workflow_request": None,
            "git_workflow_request": request,
            "response_type": "message",
            "response": "Okay, I cancelled the pending Git workflow command.",
        }

    if request.get("missing") or not request.get("command"):
        return {
            "pending_git_workflow_request": request,
            "git_workflow_request": request,
            "response_type": "clarification",
            "response": request.get("clarification_question") or clarification_for_git_workflow_request(request),
        }

    command = request["command"]
    safety = classify_git_command_safety(command)
    request["safety"] = safety

    if safety["is_dangerous"] and request.get("approved") is not True:
        request["awaiting_confirmation"] = True
        return {
            "pending_git_workflow_request": request,
            "git_workflow_request": request,
            "response_type": "confirmation",
            "response": confirmation_for_git_command(command, safety),
        }

    try:
        from ..gitcodes.command_runner import run_command

        output = run_command(command)
    except Exception as error:
        return {
            "pending_git_workflow_request": None,
            "git_workflow_request": request,
            "response_type": "error",
            "response": f"Failed to run `{render_command(command)}`: {error}",
        }

    rendered_output = output or "(command completed with no output)"
    return {
        "pending_git_workflow_request": None,
        "git_workflow_request": request,
        "response_type": "command_output",
        "response": f"Ran `{render_command(command)}`:\n\n```text\n{rendered_output}\n```",
    }

def out_of_scope_node(state: ChatGraphState) -> ChatGraphState:
    return{
        "response": "I can help with Git/GitHub questions or PromptGitX CLI usage right now."
    }


def route_chat_intent(state):
    return state.get("intent", "out_of_scope")

def create_chat_graph():
    graph = StateGraph(ChatGraphState)
    graph.add_node("classify_chat_intent", classify_chat_intent_node)
    graph.add_node("git_github_question", git_github_question_node)
    graph.add_node("promptgitx_query", promptgitx_query_node)
    graph.add_node("promptgitx_report_generation", promptgitx_report_generation_node)
    graph.add_node("git_workflow_execution", git_workflow_execution_node)
    graph.add_node("out_of_scope", out_of_scope_node)

    graph.add_edge(START, "classify_chat_intent")

    graph.add_conditional_edges(
        "classify_chat_intent",
        route_chat_intent,
        {
            "git_workflow_execution": "git_workflow_execution",
            "git_github_question": "git_github_question",
            "promptgitx_query": "promptgitx_query",
            "promptgitx_report_generation": "promptgitx_report_generation",
            "out_of_scope": "out_of_scope",
        },
    )

    graph.add_edge("git_workflow_execution", END)
    graph.add_edge("git_github_question", END)
    graph.add_edge("promptgitx_query", END)
    graph.add_edge("promptgitx_report_generation", END)
    graph.add_edge("out_of_scope", END)

    return graph.compile()

def run_chat_graph(initial_state: ChatGraphState) -> ChatGraphState:
    graph = create_chat_graph()
    return graph.invoke(initial_state)
