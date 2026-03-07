"""LLM cost calculation based on model and token counts."""

from __future__ import annotations

# Pricing per 1M tokens (input/output) as of 2025
# Source: provider pricing pages
MODEL_PRICING: dict[str, dict[str, float]] = {
    # Anthropic
    "anthropic/claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "anthropic/claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "anthropic/claude-haiku-4-20250514": {"input": 0.80, "output": 4.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-20250514": {"input": 0.80, "output": 4.0},
    # OpenAI
    "openai/gpt-4o": {"input": 2.50, "output": 10.0},
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 2.50, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    # Together / Open source
    "together_ai/meta-llama/Llama-3-70b-chat-hf": {"input": 0.90, "output": 0.90},
    "together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1": {"input": 0.60, "output": 0.60},
    # Groq
    "groq/llama3-70b-8192": {"input": 0.59, "output": 0.79},
    "groq/mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
}

# Default fallback pricing (conservative estimate)
DEFAULT_PRICING = {"input": 3.0, "output": 15.0}


def calculate_cost(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate the USD cost for an LLM call.

    Args:
        model: The model identifier (e.g., "anthropic/claude-sonnet-4-20250514").
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Cost in USD.
    """
    pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
