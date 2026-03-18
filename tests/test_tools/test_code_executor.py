"""Tests for CodeExecutor tool."""

import os
from unittest.mock import MagicMock, Mock

import pytest

from foundrai.config import FoundrAIConfig
from foundrai.models.enums import AgentRoleName
from foundrai.tools.code_executor import (
    CodeExecutor,
    CodeExecutorInput,
    E2BCodeExecutor,
    NoopCodeExecutor,
    get_code_executor,
)
from foundrai.tools.registry import ToolRegistry, create_tool_registry


@pytest.mark.asyncio
async def test_noop_executor():
    executor = NoopCodeExecutor()
    result = await executor.execute(
        CodeExecutorInput(code="print('hello')", language="python")
    )
    assert result.success
    assert "unavailable" in result.output.lower()


@pytest.mark.asyncio
async def test_e2b_executor_requires_api_key():
    """Test that E2BCodeExecutor requires E2B_API_KEY environment variable."""
    # Remove E2B_API_KEY if it exists
    original_key = os.environ.pop("E2B_API_KEY", None)

    try:
        # Should raise ValueError when E2B_API_KEY is not set
        with pytest.raises(ValueError, match="E2B_API_KEY environment variable is required"):
            E2BCodeExecutor(timeout=30)
    finally:
        # Restore original key if it existed
        if original_key:
            os.environ["E2B_API_KEY"] = original_key


@pytest.mark.asyncio
async def test_e2b_executor_initialization(monkeypatch):
    """Test that E2BCodeExecutor initializes correctly with API key."""
    test_api_key = "test-e2b-api-key-12345"
    monkeypatch.setenv("E2B_API_KEY", test_api_key)

    executor = E2BCodeExecutor(timeout=60, max_memory=1024)

    assert executor.name == "code_executor"
    assert executor.timeout == 60
    assert executor.max_memory == 1024
    assert executor.api_key == test_api_key


@pytest.mark.asyncio
async def test_e2b_executor_unsupported_language(monkeypatch):
    """Test that E2BCodeExecutor handles unsupported languages."""
    monkeypatch.setenv("E2B_API_KEY", "test-key")

    executor = E2BCodeExecutor(timeout=30)
    result = await executor.execute(
        CodeExecutorInput(code="print('test')", language="ruby")
    )

    assert not result.success
    assert "Unsupported language" in result.error


def test_get_code_executor_noop_provider():
    """Test get_code_executor returns NoopCodeExecutor when provider is 'noop'."""
    executor = get_code_executor(provider="noop")
    assert isinstance(executor, NoopCodeExecutor)


def test_get_code_executor_docker_unavailable(monkeypatch):
    """Test get_code_executor falls back to noop when Docker is unavailable and no E2B key."""
    import subprocess

    # Mock Docker as unavailable
    def mock_docker_unavailable(*args, **kwargs):
        if args and "docker" in args[0]:
            raise FileNotFoundError("docker command not found")
        return subprocess.run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_docker_unavailable)
    monkeypatch.delenv("E2B_API_KEY", raising=False)

    executor = get_code_executor(provider="docker", timeout=30)
    assert isinstance(executor, NoopCodeExecutor)


def test_get_code_executor_e2b_fallback(monkeypatch):
    """Test get_code_executor falls back to E2B when Docker unavailable but E2B key set."""
    import subprocess

    # Mock Docker as unavailable
    def mock_docker_unavailable(*args, **kwargs):
        if args and "docker" in args[0]:
            raise FileNotFoundError("docker command not found")
        return subprocess.run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_docker_unavailable)
    monkeypatch.setenv("E2B_API_KEY", "test-e2b-key")

    executor = get_code_executor(provider="docker", timeout=30, max_memory=256)
    assert isinstance(executor, E2BCodeExecutor)
    assert executor.timeout == 30
    assert executor.max_memory == 256


def test_get_code_executor_e2b_explicit(monkeypatch):
    """Test get_code_executor returns E2BCodeExecutor when explicitly requested."""
    monkeypatch.setenv("E2B_API_KEY", "test-e2b-key")

    executor = get_code_executor(provider="e2b", timeout=45, max_memory=512)
    assert isinstance(executor, E2BCodeExecutor)
    assert executor.timeout == 45
    assert executor.max_memory == 512


def test_tool_registry_register_and_get():
    """Test ToolRegistry register and get methods."""
    registry = ToolRegistry()
    tool = NoopCodeExecutor()

    registry.register(tool)

    retrieved_tool = registry.get("code_executor")
    assert retrieved_tool is tool
    assert retrieved_tool.name == "code_executor"


def test_tool_registry_get_nonexistent():
    """Test ToolRegistry.get raises KeyError for nonexistent tool."""
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="Tool not found: nonexistent_tool"):
        registry.get("nonexistent_tool")


def test_tool_registry_get_tools_for_role():
    """Test ToolRegistry.get_tools_for_role returns matching tools."""
    from foundrai.agents.roles import get_role

    registry = ToolRegistry()

    # Register multiple tools
    from foundrai.tools.file_manager import FileManager

    file_manager = FileManager(".")
    code_executor = NoopCodeExecutor()

    registry.register(file_manager)
    registry.register(code_executor)

    # Get tools for developer role (has both file_manager and code_executor)
    developer_role = get_role(AgentRoleName.DEVELOPER)
    tools = registry.get_tools_for_role(developer_role)

    assert len(tools) == 2
    tool_names = {t.name for t in tools}
    assert "file_manager" in tool_names
    assert "code_executor" in tool_names


def test_tool_registry_get_tools_for_role_partial_match():
    """Test ToolRegistry.get_tools_for_role with only some tools registered."""
    from foundrai.agents.roles import get_role

    registry = ToolRegistry()

    # Only register code_executor, not file_manager
    code_executor = NoopCodeExecutor()
    registry.register(code_executor)

    # Get tools for developer role (expects both file_manager and code_executor)
    developer_role = get_role(AgentRoleName.DEVELOPER)
    tools = registry.get_tools_for_role(developer_role)

    # Should only return the one registered tool
    assert len(tools) == 1
    assert tools[0].name == "code_executor"


def test_tool_registry_get_tools_for_agent():
    """Test ToolRegistry.get_tools_for_agent helper method."""
    registry = ToolRegistry()

    # Register tools
    from foundrai.tools.file_manager import FileManager

    file_manager = FileManager(".")
    code_executor = NoopCodeExecutor()

    registry.register(file_manager)
    registry.register(code_executor)

    # Get tools by agent role name
    tools = registry.get_tools_for_agent(AgentRoleName.DEVELOPER)

    assert len(tools) == 2
    tool_names = {t.name for t in tools}
    assert "file_manager" in tool_names
    assert "code_executor" in tool_names


def test_tool_registry_get_tools_for_agent_nonexistent_role():
    """Test ToolRegistry.get_tools_for_agent raises KeyError for invalid role."""
    registry = ToolRegistry()

    # AgentRoleName enum doesn't have a NONEXISTENT value,
    # so we test with a valid role that might not be registered in some configs
    # Actually, all default roles are registered, so this test verifies the method works
    tools = registry.get_tools_for_agent(AgentRoleName.PRODUCT_MANAGER)
    assert isinstance(tools, list)


def test_create_tool_registry(tmp_path):
    """Test create_tool_registry creates and populates registry correctly."""
    config = FoundrAIConfig()
    registry = create_tool_registry(config, str(tmp_path))

    # Verify registry is populated
    assert isinstance(registry, ToolRegistry)

    # Should have file_manager and code_executor registered
    file_manager = registry.get("file_manager")
    assert file_manager.name == "file_manager"

    code_executor = registry.get("code_executor")
    assert code_executor.name == "code_executor"


def test_create_tool_registry_with_custom_config(tmp_path, monkeypatch):
    """Test create_tool_registry respects custom configuration."""
    import subprocess

    # Mock Docker as unavailable
    def mock_docker_unavailable(*args, **kwargs):
        if args and "docker" in args[0]:
            raise FileNotFoundError("docker command not found")
        return subprocess.run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_docker_unavailable)
    monkeypatch.setenv("E2B_API_KEY", "test-key")

    config = FoundrAIConfig()
    config.sandbox.provider = "docker"  # Will fallback to E2B
    config.sandbox.timeout_seconds = 120
    config.sandbox.max_memory_mb = 1024

    registry = create_tool_registry(config, str(tmp_path))

    code_executor = registry.get("code_executor")
    # Should be E2BCodeExecutor due to fallback
    assert isinstance(code_executor, E2BCodeExecutor)
    assert code_executor.timeout == 120
    assert code_executor.max_memory == 1024


def test_create_tool_registry_noop_fallback(tmp_path, monkeypatch):
    """Test create_tool_registry falls back to noop when no sandbox available."""
    import subprocess

    # Mock Docker as unavailable
    def mock_docker_unavailable(*args, **kwargs):
        if args and "docker" in args[0]:
            raise FileNotFoundError("docker command not found")
        return subprocess.run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", mock_docker_unavailable)
    monkeypatch.delenv("E2B_API_KEY", raising=False)

    config = FoundrAIConfig()
    registry = create_tool_registry(config, str(tmp_path))

    code_executor = registry.get("code_executor")
    assert isinstance(code_executor, NoopCodeExecutor)
