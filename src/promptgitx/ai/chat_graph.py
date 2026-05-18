from langgraph.graph import StateGraph, END, START
from .graph_state import ChatGraphState

def classify_chat_intent_node(state):
    pass

def git_github_question_node(state):
    pass

def promptgitx_query_node(state):
    pass

def git_workflow_execution_node(state):
    return{
        "response": "This Feature is Currently Under Development."
    }

def out_of_scope_node(state):
    return{
        "response": "I can help with Git/GitHub questions or PromptGitX CLI usage right now."
    }


# Graph Builder
def route_chat_intent(state):
    return state.get("intent", "out_of_scope")

def build_chat_graph():
    graph = StateGraph(ChatGraphState)
    graph.add_node("classify_chat_intent", classify_chat_intent_node)
    graph.add_node("git_github_question", git_github_question_node)
    graph.add_node("promptgitx_query", promptgitx_query_node)
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
            "out_of_scope": "out_of_scope",
        },
    )

    graph.add_edge("git_workflow_execution", END)
    graph.add_edge("git_github_question", END)
    graph.add_edge("promptgitx_query", END)
    graph.add_edge("out_of_scope", END)

    return graph.compile()

