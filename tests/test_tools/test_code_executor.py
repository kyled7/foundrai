"""Tests for CodeExecutor tool."""

import pytest

from foundrai.tools.code_executor import CodeExecutorInput, NoopCodeExecutor


@pytest.mark.asyncio
async def test_noop_executor():
    executor = NoopCodeExecutor()
    result = await executor.execute(
        CodeExecutorInput(code="print('hello')", language="python")
    )
    assert result.success
    assert "unavailable" in result.output.lower()
