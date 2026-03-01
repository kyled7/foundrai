"""LiteLLM wrapper for agent LLM calls."""

from __future__ import annotations

from pydantic import BaseModel


class LLMConfig(BaseModel):
    """Per-agent LLM configuration."""

    model: str = "anthropic/claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7


class LLMResponse(BaseModel):
    """Response from an LLM call."""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""


class LLMClient:
    """Thin wrapper around LiteLLM for model-agnostic LLM calls."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.total_tokens_used: int = 0

    async def completion(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        **kwargs: object,
    ) -> LLMResponse:
        """Call the LLM via LiteLLM."""
        import litellm

        response = await litellm.acompletion(
            model=self.config.model,
            messages=messages,
            temperature=temperature or self.config.temperature,
            max_tokens=max_tokens or self.config.max_tokens,
            response_format=response_format,
        )

        usage = response.usage
        self.total_tokens_used += usage.total_tokens

        return LLMResponse(
            content=response.choices[0].message.content,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            model=response.model,
        )

    def get_model(self) -> object:
        """Return a LangChain-compatible chat model backed by LiteLLM."""
        from langchain_community.chat_models import ChatLiteLLM

        return ChatLiteLLM(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
