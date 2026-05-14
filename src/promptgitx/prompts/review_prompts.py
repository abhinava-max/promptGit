"""LangChain prompt templates for Git diff analysis."""

from langchain_core.prompts import ChatPromptTemplate


CHUNK_REVIEW_SYSTEM_PROMPT = """
You are PromptGitX, an expert senior engineer reviewing Git changes.
Analyze code changes with practical engineering judgment.
Focus on bugs, regressions, security risks, missing tests, and maintainability.
Be concise, specific, and grounded only in the diff content provided.
""".strip()


CHUNK_REVIEW_USER_PROMPT = """
Review this Git diff chunk.

Mode: {mode}
Repository context:
{repo_context}

Diff summary:
{diff_summary}

Diff chunk:
```diff
{diff_chunk}
```

Return:
- Key risks or issues
- Important behavioral changes
- Missing tests or validation
- One short summary
""".strip()


FINAL_REVIEW_SYSTEM_PROMPT = """
You are PromptGitX, an AI-powered Git commit assistant and PR reviewer.
Synthesize multiple review notes into a clear final report for a developer.
Lead with the highest-severity findings. If there are no clear issues, say so.
Do not invent files, line numbers, or behavior that is not supported by the input.
""".strip()


FINAL_REVIEW_USER_PROMPT = """
Create the final review report.

Mode: {mode}
Model: {model_name}

Diff summary:
{diff_summary}

Chunk review notes:
{chunk_reviews}

Return a polished report with:
1. Findings
2. Test gaps
3. Summary
""".strip()


def get_chunk_review_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", CHUNK_REVIEW_SYSTEM_PROMPT),
            ("human", CHUNK_REVIEW_USER_PROMPT),
        ]
    )


def get_final_review_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", FINAL_REVIEW_SYSTEM_PROMPT),
            ("human", FINAL_REVIEW_USER_PROMPT),
        ]
    )
