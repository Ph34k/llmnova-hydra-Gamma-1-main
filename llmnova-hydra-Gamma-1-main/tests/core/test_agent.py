
import pytest
from unittest.mock import MagicMock
from gamma_engine.core.agent import Agent
from gamma_engine.interfaces.tool import ToolInterface

class MockTool(ToolInterface):
    def __init__(self, name="mock_tool", result="success"):
        self.name = name
        self.description = "A mock tool"
        self.result = result
        self.schema = {"name": name, "description": "A mock tool"}

    def execute(self, **kwargs):
        return self.result

    def to_schema(self):
        return self.schema

@pytest.fixture
def mock_llm():
    return MagicMock()

@pytest.fixture
def agent(mock_llm):
    tools = [MockTool(name="test_tool")]
    return Agent(tools=tools, llm_provider=mock_llm, session_id="test_session")

def test_agent_initialization(agent):
    assert agent.session_id == "test_session"
    assert "test_tool" in agent.tools
    assert len(agent.tool_schemas) == 1

@pytest.mark.asyncio
async def test_agent_run(agent):
    response = await agent.run("Hello")
    assert response == "Agent received: Hello"

@pytest.mark.asyncio
async def test_agent_execute_tool_success(agent):
    result = await agent.execute_tool("test_tool", arg="value")
    assert result == "success"

@pytest.mark.asyncio
async def test_agent_execute_tool_not_found(agent):
    result = await agent.execute_tool("non_existent_tool")
    assert result is None

def test_agent_add_message(agent):
    agent.add_message("user", "hello")
    # Basic check to ensure no exception, as memory is mocked or internal
    assert len(agent.memory.memories) == 1
    assert agent.memory.memories[0]['content'] == "hello"
