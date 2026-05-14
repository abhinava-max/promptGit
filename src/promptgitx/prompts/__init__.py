"""Prompt templates used by PromptGitX AI workflows."""

from .review_prompts import (
    CHUNK_REVIEW_SYSTEM_PROMPT,
    CHUNK_REVIEW_USER_PROMPT,
    FINAL_REVIEW_SYSTEM_PROMPT,
    FINAL_REVIEW_USER_PROMPT,
    get_chunk_review_prompt,
    get_final_review_prompt,
)

__all__ = [
    "CHUNK_REVIEW_SYSTEM_PROMPT",
    "CHUNK_REVIEW_USER_PROMPT",
    "FINAL_REVIEW_SYSTEM_PROMPT",
    "FINAL_REVIEW_USER_PROMPT",
    "get_chunk_review_prompt",
    "get_final_review_prompt",
]
