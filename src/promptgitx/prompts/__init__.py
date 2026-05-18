"""Prompt templates used by PromptGitX AI workflows."""

from .review_prompts import (
    CHUNK_REVIEW_SYSTEM_PROMPT,
    CHUNK_REVIEW_USER_PROMPT,
    FINAL_REVIEW_SYSTEM_PROMPT,
    FINAL_REVIEW_USER_PROMPT,
    REPORT_REFINEMENT_SYSTEM_PROMPT,
    REPORT_REFINEMENT_USER_PROMPT,
    get_chunk_review_prompt,
    get_final_review_prompt,
    get_report_refinement_prompt,
)

from .chat_agent_prompts import (
    CHAT_PROMPTGITX_ASSISTANT_SYSTEM_PROMPT,
    get_chat_help_prompt,
)
__all__ = [
    "CHUNK_REVIEW_SYSTEM_PROMPT",
    "CHUNK_REVIEW_USER_PROMPT",
    "FINAL_REVIEW_SYSTEM_PROMPT",
    "FINAL_REVIEW_USER_PROMPT",
    "REPORT_REFINEMENT_SYSTEM_PROMPT",
    "REPORT_REFINEMENT_USER_PROMPT",
    "get_chunk_review_prompt",
    "get_final_review_prompt",
    "get_report_refinement_prompt",
    "CHAT_PROMPTGITX_ASSISTANT_SYSTEM_PROMPT",
    "get_chat_help_prompt",
]
