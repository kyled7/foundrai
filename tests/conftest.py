"""Shared test fixtures for FoundrAI."""

from __future__ import annotations

import pytest
import pytest_asyncio

from foundrai.agents.llm import LLMResponse
from foundrai.persistence.database import Database


class MockLLMClient:
    """Mock LLM client that returns pre-configured responses."""

    def __init__(self) -> None:
        self._responses: list[str] = []
        self._call_index = 0
        self.total_tokens_used = 0

    def add_response(self, content: str) -> None:
        """Add a response to the queue."""
        self._responses.append(content)

    async def completion(self, messages: list, **kwargs: object) -> LLMResponse:
        """Return next pre-configured response."""
        if not self._responses:
            return LLMResponse(content="No response configured", total_tokens=0)
        response = self._responses[self._call_index % len(self._responses)]
        self._call_index += 1
        self.total_tokens_used += 100
        return LLMResponse(content=response, total_tokens=100)


@pytest.fixture
def mock_llm() -> MockLLMClient:
    """Provide a mock LLM client."""
    return MockLLMClient()


@pytest_asyncio.fixture
async def db(tmp_path):
    """Provide a temporary test database."""
    database = Database(str(tmp_path / "test.db"))
    await database.connect()
    yield database
    await database.close()
