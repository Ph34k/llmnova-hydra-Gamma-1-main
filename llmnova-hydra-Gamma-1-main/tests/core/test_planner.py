
import pytest
from unittest.mock import MagicMock
from gamma_engine.core.planner import Planner, PlanStep
from gamma_engine.interfaces.llm_provider import Message

@pytest.fixture
def mock_llm():
    return MagicMock()

def test_create_plan_success(mock_llm):
    planner = Planner(mock_llm)

    # Mock LLM response with JSON
    mock_llm.chat.return_value = Message(
        role="assistant",
        content='```json\n["Step 1", "Step 2"]\n```'
    )

    plan = planner.create_plan("My Goal")

    assert len(plan) == 2
    assert plan[0].description == "Step 1"
    assert plan[0].id == 1
    assert plan[0].status == "pending"

def test_create_plan_fallback(mock_llm):
    planner = Planner(mock_llm)

    # Mock LLM returning bad JSON
    mock_llm.chat.return_value = Message(
        role="assistant",
        content="Not JSON"
    )

    plan = planner.create_plan("My Goal")

    # Should fallback to single step
    assert len(plan) == 1
    assert plan[0].description == "My Goal"

def test_update_step():
    planner = Planner(MagicMock())
    planner.plan = [PlanStep(id=1, description="Task")]

    planner.update_step(1, "completed", "Done")

    assert planner.plan[0].status == "completed"
    assert planner.plan[0].result == "Done"

def test_get_next_step():
    planner = Planner(MagicMock())
    step1 = PlanStep(id=1, description="Task 1", status="completed")
    step2 = PlanStep(id=2, description="Task 2", status="pending")
    planner.plan = [step1, step2]

    next_step = planner.get_next_step()
    assert next_step.id == 2
    assert next_step.description == "Task 2"
