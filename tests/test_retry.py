"""Tests for retry utility with exponential backoff."""

from __future__ import annotations

import asyncio

import pytest

from foundrai.utils.retry import (
    classify_error,
    is_retryable_error,
    retry_async,
)


def test_classify_error_rate_limit() -> None:
    """Test classification of rate limit errors."""
    assert classify_error(Exception("rate limit exceeded")) == "rate_limit"
    assert classify_error(Exception("429 too many requests")) == "rate_limit"
    assert classify_error(Exception("API rate_limit reached")) == "rate_limit"


def test_classify_error_timeout() -> None:
    """Test classification of timeout errors."""
    assert classify_error(TimeoutError("timed out")) == "timeout"
    assert classify_error(Exception("request timeout")) == "timeout"
    assert classify_error(TimeoutError("async timeout")) == "timeout"


def test_classify_error_context_overflow() -> None:
    """Test classification of context overflow errors."""
    assert classify_error(Exception("context token limit exceeded")) == "context_overflow"
    assert classify_error(Exception("token limit overflow")) == "context_overflow"
    assert classify_error(Exception("context size exceeds maximum")) == "context_overflow"


def test_classify_error_parse_error() -> None:
    """Test classification of parse errors."""
    assert classify_error(Exception("json decode error")) == "parse_error"
    assert classify_error(Exception("parse failure")) == "parse_error"
    assert classify_error(Exception("JSON parsing failed")) == "parse_error"


def test_classify_error_tool_error() -> None:
    """Test classification of tool errors."""
    assert classify_error(Exception("tool call failed")) == "tool_error"
    assert classify_error(Exception("function call error")) == "tool_error"


def test_classify_error_unknown() -> None:
    """Test classification of unknown errors."""
    assert classify_error(Exception("something random")) == "unknown"
    assert classify_error(ValueError("invalid value")) == "unknown"


def test_is_retryable_error() -> None:
    """Test retryable error classification."""
    # Retryable errors
    assert is_retryable_error("rate_limit") is True
    assert is_retryable_error("timeout") is True

    # Non-retryable errors
    assert is_retryable_error("context_overflow") is False
    assert is_retryable_error("tool_error") is False
    assert is_retryable_error("parse_error") is False
    assert is_retryable_error("unknown") is False


@pytest.mark.asyncio
async def test_retry_async_success() -> None:
    """Test retry with a function that succeeds on first try."""
    call_count = 0

    async def succeed() -> str:
        nonlocal call_count
        call_count += 1
        return "success"

    result = await retry_async(succeed, max_retries=3)
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_async_eventual_success() -> None:
    """Test retry with a function that fails then succeeds."""
    call_count = 0

    async def fail_twice() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("temporary failure")
        return "success"

    result = await retry_async(
        fail_twice,
        max_retries=3,
        backoff_base=0.01,  # Fast backoff for testing
    )
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_async_max_retries_exceeded() -> None:
    """Test retry when max retries is exceeded."""
    call_count = 0

    async def always_fail() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("permanent failure")

    with pytest.raises(ValueError, match="permanent failure"):
        await retry_async(
            always_fail,
            max_retries=2,
            backoff_base=0.01,
        )
    assert call_count == 3  # Initial + 2 retries


@pytest.mark.asyncio
async def test_retry_async_auto_classify_retryable() -> None:
    """Test auto-classification of retryable errors."""
    call_count = 0

    async def rate_limit_then_succeed() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("rate limit exceeded")
        return "success"

    result = await retry_async(
        rate_limit_then_succeed,
        max_retries=3,
        backoff_base=0.01,
        auto_classify_retryable=True,
    )
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_async_auto_classify_non_retryable() -> None:
    """Test auto-classification of non-retryable errors."""
    call_count = 0

    async def parse_error() -> None:
        nonlocal call_count
        call_count += 1
        raise Exception("json decode error")

    # Non-retryable error should fail immediately without retries
    with pytest.raises(Exception, match="json decode error"):
        await retry_async(
            parse_error,
            max_retries=3,
            backoff_base=0.01,
            auto_classify_retryable=True,
        )
    assert call_count == 1  # No retries for non-retryable error


@pytest.mark.asyncio
async def test_retry_async_timeout_is_retryable() -> None:
    """Test that timeout errors are retried when auto-classify is enabled."""
    call_count = 0

    async def timeout_then_succeed() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise TimeoutError("request timed out")
        return "success"

    result = await retry_async(
        timeout_then_succeed,
        max_retries=3,
        backoff_base=0.01,
        auto_classify_retryable=True,
    )
    assert result == "success"
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_async_exponential_backoff() -> None:
    """Test that exponential backoff increases wait time."""
    call_count = 0
    timestamps: list[float] = []

    async def fail_three_times() -> str:
        nonlocal call_count
        call_count += 1
        timestamps.append(asyncio.get_event_loop().time())
        if call_count < 4:
            raise Exception("temporary failure")
        return "success"

    result = await retry_async(
        fail_three_times,
        max_retries=3,
        backoff_base=0.05,
    )
    assert result == "success"
    assert call_count == 4

    # Verify exponential backoff (0.05, 0.10, 0.20 seconds)
    # Allow some tolerance for timing
    wait1 = timestamps[1] - timestamps[0]
    wait2 = timestamps[2] - timestamps[1]
    wait3 = timestamps[3] - timestamps[2]

    assert 0.04 < wait1 < 0.08  # ~0.05s
    assert 0.08 < wait2 < 0.15  # ~0.10s
    assert 0.15 < wait3 < 0.30  # ~0.20s


@pytest.mark.asyncio
async def test_retry_async_specific_exception_types() -> None:
    """Test retrying only specific exception types."""
    call_count = 0

    async def raise_value_error() -> None:
        nonlocal call_count
        call_count += 1
        raise ValueError("specific error")

    # ValueError not in retryable_exceptions, should not retry
    with pytest.raises(ValueError, match="specific error"):
        await retry_async(
            raise_value_error,
            max_retries=3,
            retryable_exceptions=(TimeoutError,),
        )
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_async_context_overflow_not_retried() -> None:
    """Test that context overflow errors are not retried."""
    call_count = 0

    async def context_overflow() -> None:
        nonlocal call_count
        call_count += 1
        raise Exception("context token limit exceeded")

    with pytest.raises(Exception, match="context token limit exceeded"):
        await retry_async(
            context_overflow,
            max_retries=3,
            backoff_base=0.01,
            auto_classify_retryable=True,
        )
    assert call_count == 1  # No retries for context overflow
