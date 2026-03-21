"""LiteLLM wrapper for agent LLM calls with tool use support."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Per-agent LLM configuration."""

    model: str = "anthropic/claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7


class LLMResponse(BaseModel):
    """Response from an LLM call, including optional tool calls."""

    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = ""
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class LLMClient:
    """Thin wrapper around LiteLLM for model-agnostic LLM calls."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.model = config.model
        self.total_tokens_used: int = 0

    async def completion(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        **kwargs: object,
    ) -> LLMResponse:
        """Call the LLM via LiteLLM, optionally with tool schemas."""
        import litellm

        call_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }
        if response_format:
            call_kwargs["response_format"] = response_format
        if tools:
            call_kwargs["tools"] = tools

        response = await litellm.acompletion(**call_kwargs)

        usage = response.usage
        self.total_tokens_used += usage.total_tokens

        # Extract tool calls if present
        message = response.choices[0].message
        tool_calls: list[dict[str, Any]] = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                import json

                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                tool_calls.append(
                    {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": args,
                    }
                )

        return LLMResponse(
            content=message.content or "",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            model=response.model,
            tool_calls=tool_calls,
        )

    def get_model(self) -> object:
        """Return a LangChain-compatible chat model backed by LiteLLM."""
        from langchain_community.chat_models import ChatLiteLLM

        return ChatLiteLLM(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
