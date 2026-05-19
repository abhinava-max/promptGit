"""Resolve configured LLMs for PromptGitX."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..config.paths import get_config_env_path

PROVIDER_TO_LANGCHAIN = {
    "GROQ": "groq",
    "OPENAI": "openai",
    "ANTHROPIC": "anthropic",
    "GEMINI": "google_genai",
    "OLLAMA": "ollama",
}

PROVIDER_API_KEYS = {
    "GROQ": "GROQ_API_KEY",
    "OPENAI": "OPENAI_API_KEY",
    "ANTHROPIC": "ANTHROPIC_API_KEY",
    "GEMINI": "GEMINI_API_KEY",
}

PROVIDER_BASE_URLS = {
    "OLLAMA": "OLLAMA_BASE_URL",
}


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model: str
    index: int
    langchain_provider: str
    api_key: str | None = None
    base_url: str | None = None

    @property
    def display_name(self) -> str:
        return f"{self.provider} | {self.model}"

    @property
    def langchain_model_name(self) -> str:
        return f"{self.langchain_provider}:{self.model}"


@dataclass(frozen=True)
class LLMConfig:
    provider: str | None
    models: list[ModelSpec]

    @property
    def primary_model(self) -> ModelSpec | None:
        return self.models[0] if self.models else None


class RuntimeModelRouter:
    def __init__(self, *, temperature: float = 0, **kwargs: Any):
        self.config = get_active_llm_config()

        if not self.config.models:
            raise RuntimeError("No LLM provider is configured. Run `promptgitx config` first.")

        self.temperature = temperature
        self.kwargs = kwargs
        self.model_index = 0

    @property
    def current_model(self) -> ModelSpec:
        return self.config.models[self.model_index]

    def has_next_model(self) -> bool:
        return self.model_index + 1 < len(self.config.models)

    def advance_model(self) -> ModelSpec:
        if not self.has_next_model():
            raise RuntimeError("All configured LLM models failed for this review run.")

        self.model_index += 1
        return self.current_model

    def create_current_chat_model(self):
        return create_chat_model(
            self.current_model,
            temperature=self.temperature,
            **self.kwargs,
        )


def read_env(env_path: Path | None = None) -> dict[str, str]:
    if env_path is None:
        env_path = get_config_env_path()

    env_data: dict[str, str] = {}

    if not env_path.exists():
        return env_data

    with env_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            env_data[key.strip()] = value.strip()

    return env_data


def load_env_into_process(env_data: dict[str, str]) -> None:
    for key, value in env_data.items():
        if value:
            os.environ.setdefault(key, value)

    if env_data.get("GEMINI_API_KEY"):
        os.environ.setdefault("GOOGLE_API_KEY", env_data["GEMINI_API_KEY"])


def get_active_llm_config(env_path: Path | None = None) -> LLMConfig:
    env_data = read_env(env_path)
    load_env_into_process(env_data)

    provider = env_data.get("CURRENT_PROVIDER", "").upper().strip()

    if provider not in PROVIDER_TO_LANGCHAIN:
        return LLMConfig(provider=None, models=[])

    api_key = env_data.get(PROVIDER_API_KEYS.get(provider, ""))
    base_url = env_data.get(PROVIDER_BASE_URLS.get(provider, ""))
    langchain_provider = PROVIDER_TO_LANGCHAIN[provider]
    models: list[ModelSpec] = []

    for index in range(1, 6):
        model = env_data.get(f"{provider}_MODEL_{index}", "").strip()

        if not model:
            continue

        models.append(
            ModelSpec(
                provider=provider,
                model=model,
                index=index,
                langchain_provider=langchain_provider,
                api_key=api_key or None,
                base_url=base_url or None,
            )
        )

    return LLMConfig(provider=provider, models=models)


def get_current_model_name(env_path: Path | None = None) -> str | None:
    config = get_active_llm_config(env_path)

    if not config.primary_model:
        return None

    return config.primary_model.display_name


def get_current_model_display(env_path: Path | None = None) -> str:
    return get_current_model_name(env_path) or "Not configured"


def create_chat_model(
    model_spec: ModelSpec | None = None,
    *,
    temperature: float = 0,
    **kwargs: Any,
):
    from langchain.chat_models import init_chat_model

    if model_spec is None:
        model_spec = get_active_llm_config().primary_model

    if model_spec is None:
        raise RuntimeError("No LLM provider is configured. Run `promptgitx config` first.")

    init_kwargs: dict[str, Any] = {
        "model": model_spec.langchain_model_name,
        "temperature": temperature,
        **kwargs,
    }

    if model_spec.api_key:
        init_kwargs["api_key"] = model_spec.api_key

    if model_spec.base_url:
        init_kwargs["base_url"] = model_spec.base_url

    return init_chat_model(**init_kwargs)


def create_chat_model_with_fallbacks(*, temperature: float = 0, **kwargs: Any):
    config = get_active_llm_config()

    if not config.primary_model:
        raise RuntimeError("No LLM provider is configured. Run `promptgitx config` first.")

    primary = create_chat_model(config.primary_model, temperature=temperature, **kwargs)
    fallback_models = [
        create_chat_model(model, temperature=temperature, **kwargs)
        for model in config.models[1:]
    ]

    if not fallback_models:
        return primary

    return primary.with_fallbacks(fallback_models)


def get_model_rotation_middleware() -> Callable[..., Any]:
    from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call

    config = get_active_llm_config()
    model_specs = config.models

    @wrap_model_call
    def rotate_model_on_request(
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        model_index = getattr(request.runtime.context, "model_index", 0)
        model_spec = model_specs[model_index] if model_specs else None

        if model_spec is None:
            return handler(request)

        model = create_chat_model(model_spec)
        return handler(request.override(model=model))

    return rotate_model_on_request
