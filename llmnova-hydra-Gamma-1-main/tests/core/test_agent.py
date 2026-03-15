
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
    import uuid
    tools = [MockTool(name="test_tool")]
    # Use unique session to avoid state pollution between tests (since Memory persists to file)
    return Agent(tools=tools, llm_provider=mock_llm, session_id=str(uuid.uuid4()))

def test_agent_initialization(agent):
    # Session ID is random uuid in fixture, so just check type or presence
    assert agent.session_id is not None
    assert "test_tool" in agent.tools
    assert len(agent.tool_schemas) == 1

@pytest.mark.asyncio
async def test_agent_run(agent):
    # Mock the LLM to return a final answer
    from gamma_engine.interfaces.llm_provider import Message
    agent.llm.chat.return_value = Message(role="assistant", content="Final Answer")

    response = await agent.run("Hello")
    assert response == "Final Answer"

@pytest.mark.asyncio
async def test_agent_execute_tool_success(agent):
    result = await agent.execute_tool("test_tool", arg="value")
    assert result == "success"

@pytest.mark.asyncio
async def test_agent_execute_tool_not_found(agent):
    result = await agent.execute_tool("non_existent_tool")
    assert "Error" in result

def test_agent_add_message(agent):
    agent.add_message("user", "hello")
    # Using 'messages' as EpisodicMemory uses 'messages' list, not 'memories'
    assert len(agent.memory.messages) == 1
    assert agent.memory.messages[0].content == "hello"
