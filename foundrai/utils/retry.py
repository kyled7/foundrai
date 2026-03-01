"""Retry utility with exponential backoff."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


async def retry_async(
    fn: Callable[..., Any],
    max_retries: int = 3,
    backoff_base: float = 1.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Any:
    """Retry an async function with exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_error = e
            if attempt < max_retries:
                wait = backoff_base * (2 ** attempt)
                await asyncio.sleep(wait)
    raise last_error  # type: ignore[misc]
