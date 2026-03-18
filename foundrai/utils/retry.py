"""Retry utility with exponential backoff."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def classify_error(exception: Exception) -> str:
    """Auto-classify an exception into an error type.

    Returns one of: rate_limit, context_overflow, timeout, tool_error,
    parse_error, or unknown.
    """
    msg = str(exception).lower()
    exc_type = type(exception).__name__.lower()

    if "rate" in msg or "rate_limit" in msg or "429" in msg:
        return "rate_limit"
    if ("context" in msg or "token" in msg and
        ("limit" in msg or "overflow" in msg or "exceed" in msg)):
        return "context_overflow"
    if ("timeout" in msg or "timed out" in msg or
        exc_type in ("timeouterror", "asynciotimeouterror")):
        return "timeout"
    if "tool" in msg or "function" in msg and "call" in msg:
        return "tool_error"
    if "parse" in msg or "json" in msg or "decode" in msg:
        return "parse_error"
    return "unknown"


def is_retryable_error(error_type: str) -> bool:
    """Determine if an error type is retryable.

    Retryable errors:
    - rate_limit: Yes, with backoff
    - timeout: Yes, might succeed on retry

    Non-retryable errors:
    - context_overflow: No, need to reduce context
    - tool_error: No, tool is broken
    - parse_error: No, bad format won't fix itself
    - unknown: No, default to safe
    """
    return error_type in ("rate_limit", "timeout")


async def retry_async(
    fn: Callable[..., Any],
    max_retries: int = 3,
    backoff_base: float = 1.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
    auto_classify_retryable: bool = False,
) -> Any:
    """Retry an async function with exponential backoff.

    Args:
        fn: The async function to retry
        max_retries: Maximum number of retry attempts
        backoff_base: Base backoff time in seconds (doubles each retry)
        retryable_exceptions: Tuple of exception types to catch
        auto_classify_retryable: If True, automatically classify exceptions
            and only retry if classified as retryable

    Returns:
        The result of the function call

    Raises:
        The last exception encountered if all retries fail
    """
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_error = e
            # If auto_classify_retryable is enabled, check if error is retryable
            if auto_classify_retryable:
                error_type = classify_error(e)
                if not is_retryable_error(error_type):
                    # Non-retryable error, raise immediately
                    raise
            # Retry if we have attempts left
            if attempt < max_retries:
                wait = backoff_base * (2 ** attempt)
                await asyncio.sleep(wait)
    raise last_error  # type: ignore[misc]
