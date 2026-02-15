import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from gamma_engine.flow.planning import PlanningFlow
from gamma_engine.core.agent import Agent
from gamma_engine.tools.planning import PlanningTool
from gamma_engine.interfaces.llm_provider import Message

@pytest.fixture
def mock_agent():
    agent = MagicMock(spec=Agent)
    agent.run = AsyncMock(return_value="Step executed successfully")
    agent.llm = MagicMock()
    # Mock LLM chat response for plan creation
    mock_msg = Message(
        role="assistant",
        content=None,
        tool_calls=[{
            "id": "call_1",
            "function": {
                "name": "planning",
                "arguments": '{"command": "create", "title": "Test Plan", "steps": ["Step 1", "Step 2"]}'
            }
        }]
    )
    agent.llm.chat.return_value = mock_msg
    return agent

@pytest.fixture
def planning_flow(mock_agent):
    return PlanningFlow(primary_agent=mock_agent)

@pytest.mark.asyncio
async def test_flow_initialization(planning_flow):
    assert planning_flow.primary_agent is not None
    assert isinstance(planning_flow.planning_tool, PlanningTool)

@pytest.mark.asyncio
async def test_create_initial_plan(planning_flow, mock_agent):
    request = "Build a website"
    await planning_flow._create_initial_plan(request)

    # Check if plan exists
    assert planning_flow.active_plan_id in planning_flow.planning_tool.plans
    plan = planning_flow.planning_tool.plans[planning_flow.active_plan_id]
    assert plan["title"] == "Test Plan"
    assert len(plan["steps"]) == 2

@pytest.mark.asyncio
async def test_execute_flow(planning_flow, mock_agent):
    # Mock LLM to return tool calls for creating plan
    # And allow agent.run to succeed

    result = await planning_flow.execute("Do complex task")

    assert "Plan Execution Completed" in result
    assert "Step 1" in planning_flow.planning_tool._get_plan(planning_flow.active_plan_id)
    # Ensure agent was called for steps
    assert mock_agent.run.call_count >= 2

@pytest.mark.asyncio
async def test_fallback_plan_creation(planning_flow, mock_agent):
    # Simulate LLM failing to call tool
    mock_agent.llm.chat.return_value = Message(role="assistant", content="I cannot create a plan.")

    await planning_flow._create_initial_plan("Simple task")

    # Should create default plan with 1 step
    assert planning_flow.active_plan_id in planning_flow.planning_tool.plans
    plan = planning_flow.planning_tool.plans[planning_flow.active_plan_id]
    assert plan["title"] == "Auto-generated Plan"
    assert plan["steps"] == ["Simple task"]
