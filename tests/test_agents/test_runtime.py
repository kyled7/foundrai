"""Tests for AgentRuntime."""

from __future__ import annotations

from unittest.mock import MagicMock

from foundrai.agents.runtime import AgentRuntime, RuntimeResult


def test_runtime_result_defaults():
    result = RuntimeResult(output="test")
    assert result.success
    assert result.tokens_used == 0
    assert result.parsed is None
    assert result.artifacts == []


def test_runtime_result_with_parsed():
    result = RuntimeResult(output="test", parsed={"key": "val"}, tokens_used=100)
    assert result.parsed == {"key": "val"}
    assert result.tokens_used == 100


class TestAgentRuntimeInit:
    def test_init(self):
        llm = MagicMock()
        event_log = MagicMock()
        runtime = AgentRuntime(llm_client=llm, event_log=event_log, max_iterations=5)
        assert runtime.max_iterations == 5
        assert runtime.llm_client is llm
        assert runtime.event_log is event_log


class TestToLangchainMessages:
    def test_system_message(self):
        from langchain_core.messages import SystemMessage
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        msgs = runtime._to_langchain_messages([{"role": "system", "content": "You are helpful"}])
        assert len(msgs) == 1
        assert isinstance(msgs[0], SystemMessage)
        assert msgs[0].content == "You are helpful"

    def test_user_message(self):
        from langchain_core.messages import HumanMessage
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        msgs = runtime._to_langchain_messages([{"role": "user", "content": "Hello"}])
        assert isinstance(msgs[0], HumanMessage)

    def test_assistant_message(self):
        from langchain_core.messages import AIMessage
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        msgs = runtime._to_langchain_messages([{"role": "assistant", "content": "Hi"}])
        assert isinstance(msgs[0], AIMessage)

    def test_multiple_messages(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        msgs = runtime._to_langchain_messages([
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
            {"role": "assistant", "content": "ast"},
        ])
        assert len(msgs) == 3


class TestParseJson:
    def test_direct_json(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        result = runtime._parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_array(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        result = runtime._parse_json('[1, 2, 3]')
        assert result == [1, 2, 3]

    def test_json_in_code_block(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        content = '```json\n{"key": "value"}\n```'
        result = runtime._parse_json(content)
        assert result == {"key": "value"}

    def test_json_in_plain_code_block(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        content = '```\n{"key": "value"}\n```'
        result = runtime._parse_json(content)
        assert result == {"key": "value"}

    def test_invalid_json(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        result = runtime._parse_json("not json at all")
        assert result is None

    def test_invalid_json_in_code_block(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        result = runtime._parse_json("```json\nnot valid\n```")
        assert result is None


class TestExtractTokenUsage:
    def test_no_usage_metadata(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        result = {"messages": [MagicMock(spec=[])]}
        assert runtime._extract_token_usage(result) == 0

    def test_with_usage_metadata(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        msg = MagicMock()
        msg.usage_metadata = {"total_tokens": 150}
        result = {"messages": [msg]}
        assert runtime._extract_token_usage(result) == 150

    def test_multiple_messages_sum(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        msg1 = MagicMock()
        msg1.usage_metadata = {"total_tokens": 100}
        msg2 = MagicMock()
        msg2.usage_metadata = {"total_tokens": 50}
        result = {"messages": [msg1, msg2]}
        assert runtime._extract_token_usage(result) == 150

    def test_empty_messages(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        assert runtime._extract_token_usage({"messages": []}) == 0


class TestCollectArtifacts:
    def test_returns_empty(self):
        runtime = AgentRuntime(llm_client=MagicMock(), event_log=MagicMock())
        assert runtime._collect_artifacts({"messages": []}) == []


async def test_runtime_retries_on_failure():
    """Test that AgentRuntime retries on transient failures."""
    llm = MagicMock()
    event_log = MagicMock()
    event_log.append = MagicMock(return_value=None)

    # Mock LLM to fail twice with rate limit, then succeed
    call_count = 0

    async def mock_completion(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise Exception("Rate limit exceeded: 429")
        # Third call succeeds
        response = MagicMock()
        response.content = "Success"
        response.total_tokens = 100
        response.prompt_tokens = 50
        response.completion_tokens = 50
        response.tool_calls = None
        return response

    llm.completion = mock_completion

    runtime = AgentRuntime(llm_client=llm, event_log=event_log)
    messages = [{"role": "user", "content": "test"}]

    result = await runtime.run(messages)

    # Should succeed after retries
    assert result.success
    assert result.output == "Success"
    assert call_count == 3  # 2 failures + 1 success
