from langchain_core.output_parsers import StrOutputParser
from promptgitx.ai.llm_provider import RuntimeModelRouter
from promptgitx.misc.console import console
from promptgitx.prompts import get_chat_help_prompt


def run_help_chat() -> None:
    while True:
        user_input = console.input("\n[bold yellow]PromptGitX>[/bold yellow] ")
        if user_input.strip().lower() in ["exit", "quit", ":q"]:
            break

        response = ask_help_agent(user_input)
        console.print(f"\n[bold green]AI[/bold green] > {response}")


def ask_help_agent(user_input: str) -> str:
    prompt = get_chat_help_prompt()
    model_router = RuntimeModelRouter()
    chain = prompt | model_router.create_current_chat_model() | StrOutputParser()
    return chain.invoke(
        {"user_input": user_input}
    )