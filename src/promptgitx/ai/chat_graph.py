import re

from langgraph.graph import StateGraph, END, START
from .graph_state import ChatGraphState

from .llm_provider import RuntimeModelRouter
from .json_utils import extract_json_object
from langchain_core.output_parsers import StrOutputParser

from ..prompts import (
    get_chat_intent_prompt,
    get_git_github_question_prompt,
    get_promptgitx_help_prompt,
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
DIRECT_REPORT_ACTION_RE = re.compile(
    r"^\s*(?:please\s+)?(?:can|could|would)?\s*(?:you\s+)?"
    r"(analy[sz]e|review|compare|create|generate|make|check|scan|inspect)\b",
    re.IGNORECASE,
)
BRANCH_COMPARE_RE = re.compile(r"\b(analy[sz]e|review|compare)\b.*\bbranch(?:es)?\b", re.IGNORECASE)


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

    return has_direct_report_action and (
        has_report_target or has_pr_ordinal or has_compare_range or has_branch_compare
    )

def maybe_correct_chat_intent(intent: str, user_input: str) -> tuple[str, str | None]:
    if intent in {"promptgitx_query", "out_of_scope"} and is_direct_report_generation_request(user_input):
        return (
            "promptgitx_report_generation",
            "Corrected an action-style report request after LLM classification.",
        )

    return intent, None

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
    return {
        "response": "This Feature is Currently Under Development."
    }

def git_workflow_execution_node(state: ChatGraphState) -> ChatGraphState:
    return{
        "response": "This Feature is Currently Under Development."
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
