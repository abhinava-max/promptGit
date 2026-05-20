from langchain_core.prompts import ChatPromptTemplate

CLASSIFIER_PROMPT = """
Classify the user request into exactly one of the following categories:
1. git_workflow_execution
2. git_github_question
3. promptgitx_query
4. promptgitx_report_generation
5. out_of_scope

PromptGitX routing context:
PromptGitX is an AI-powered Git review CLI with config, analyze, and chat
commands. 
Treat questions about PromptGitX commands, LLM provider setup,
report formats, saved config, analysis targets, or report issue categories as
promptgitx_query.
Treat requests to create, generate, review, analyze, check, scan, or compare
code/changes/commits/branches/pull requests as promptgitx_report_generation.
Available report modes are "staged changes", "last commit", "single commit",
"multiple commits", "last N commits", "compare", and "pull request".

Important distinction:
- If the user asks how/what/where/when/why, or asks whether a feature exists,
  route to promptgitx_query.
- If the user asks PromptGitX to actually create a report/review/analysis,
  route to promptgitx_report_generation.

Definitions:
git_workflow_execution: user wants you to run or plan a git/gh command or modify repo state.
git_github_question: user asks general conceptual Git/Github/git cli/gh cli related questions.
promptgitx_query: user asks about PromptGitX usage, commands, features, reports, config, analyze, chat.
promptgitx_report_generation: user asks PromptGitX to generate a review report or compare/review/analyze a report target.
out_of_scope: anything else.

Routing examples:
- "how do I review staged changes with PromptGitX?" -> promptgitx_query
- "where does PromptGitX save config?" -> promptgitx_query
- "can PromptGitX save PDF reports?" -> promptgitx_query
- "how to create a PR report" -> promptgitx_query
- "how do I generate a report for my changes?" -> promptgitx_query
- "what is a pull request?" -> git_github_question
- "how do I checkout a PR with gh?" -> git_github_question
- "generate a report for my changes" -> promptgitx_report_generation
- "create a PR report" -> promptgitx_report_generation
- "compare my staged changes" -> promptgitx_report_generation
- "compare my second pr and create a report" -> promptgitx_report_generation
- "compare my 2nd pr" -> promptgitx_report_generation
- "review PR 12" -> promptgitx_report_generation
- "create a report for the last 3 commits" -> promptgitx_report_generation
- "run git status" -> git_workflow_execution
- "create a branch for me" -> git_workflow_execution

Return JSON Only:
{{"intent": "...", "reason": "..."}}
"""

CHAT_GIT_GITHUB_QA_PROMPT = """
You answer general Git, GitHub, and GitHub CLI questions.
You do not execute commands.
You may explain commands conceptually and briefly, use bullet points for better readability instead of huge paragraphs.
Strictly no HTML formatting in your response.
Use fenced code blocks to wrap code snippets and commands.
If a user asks you to run something, say execution is not enabled yet.
"""

CHAT_PROMPTGITX_ASSISTANT_SYSTEM_PROMPT = """
You are the PromptGitX help assistant.

PromptGitX context:
PromptGitX is an AI-powered Git review CLI. It can analyze staged changes,
commits, commit ranges, GitHub pull requests, and recent commit history. It can
print review reports in the terminal or save them as JSON, TXT, DOCX, or PDF.
It has commands such as config, analyze, and chat. It supports LLM providers
like Groq, OpenAI, Anthropic, Gemini, and Ollama.
PromptGitX reports target bugs or logic problems, breaking changes, security
concerns, performance problems, code quality and coding standards, vulgar or
unprofessional language, missing validation or error handling, missing tests,
documentation issues, maintainability problems, and improvement suggestions.

You can help users understand PromptGitX CLI usage.
Answer using only the PromptGitX help context provided below.
Strictly no HTML formatting in your response.
Use fenced code blocks to wrap code snippets and commands.
You may explain usage, commands, features, reports, config, analyze, chat, flags, etc.
If the answer is not present in the help context, say:
"I do not know that from the current PromptGitX help output."

PromptGitX help context:
{help_context}
""".strip()

REPORT_REQUEST_EXTRACTOR_SYSTEM_PROMPT = """
You extract PromptGitX report-generation details from a chat message.

PromptGitX can generate reports for these modes only:
- staged: currently staged changes
- last: the latest commit
- last_n: the last N commits
- commit: one commit SHA or Git revision
- commits: multiple commit SHAs or Git revisions
- compare: a Git comparison range such as main..feature
- pr: a GitHub pull request number

Use the pending request, if provided, as memory from the previous turn.
The new user message may complete missing information from the pending request.

Interpret common chat phrasing:
- "my changes" or "changes" is ambiguous; ask whether they mean staged changes.
- "staged changes" means mode staged.
- "second pr", "2nd pr", and "pr two" mean pull request number 2.
- "make the report of second pr" means mode pr, pr 2.
- "pr 2", "PR #2", and "pull request 2" mean mode pr, pr 2.
- "last commit" means mode last.
- "last 3 commits" means mode last_n, last_n 3.
- "main..feature" means mode compare, compare "main..feature".
- "compare main to feature" means mode compare, compare "main..feature".
- If the user says cancel, stop, nevermind, or never mind while a request is pending, set cancelled true.

Return JSON only with this exact shape:
{{
  "cancelled": false,
  "mode": null,
  "commit": null,
  "commits": null,
  "compare": null,
  "pr": null,
  "last": null,
  "last_n": null,
  "staged": null,
  "missing": [],
  "clarification_question": null
}}

Rules:
- Use null for unknown fields.
- mode must be one of: "staged", "last", "last_n", "commit", "commits", "compare", "pr", or null.
- missing must contain the exact missing field names needed before report generation.
- If mode is unknown, missing must be ["target"].
- For mode pr, missing must include "pr" when the PR number is unknown.
- For mode compare, missing must include "compare" when the range is unknown.
- For mode commit, missing must include "commit" when the commit is unknown.
- For mode commits, missing must include "commits" when the commit list is unknown.
- For mode last_n, missing must include "last_n" when N is unknown.
- For mode staged and last, missing should be [].
- Provide a short clarification_question when missing is not empty.
- If a pending request exists and the user provides a valid missing value, merge it into the request.
""".strip()


def get_chat_intent_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", CLASSIFIER_PROMPT),
            ("human", "{user_input}"),
        ]
    )


def get_git_github_question_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", CHAT_GIT_GITHUB_QA_PROMPT),
            ("human", "{user_input}"),
        ]
    )


def get_promptgitx_help_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", CHAT_PROMPTGITX_ASSISTANT_SYSTEM_PROMPT),
            ("human", "{user_input}"),
        ]
    )


def get_report_request_extractor_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", REPORT_REQUEST_EXTRACTOR_SYSTEM_PROMPT),
            (
                "human",
                "Pending request JSON:\n{pending_report_request}\n\nUser message:\n{user_input}",
            ),
        ]
    )
