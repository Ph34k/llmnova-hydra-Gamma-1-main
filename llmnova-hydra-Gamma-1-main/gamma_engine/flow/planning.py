import json
import time
import logging
from typing import Optional, Dict, Any, List

from .base import BaseFlow
from ..core.agent import Agent
from ..tools.planning import PlanningTool
from ..interfaces.llm_provider import Message

logger = logging.getLogger(__name__)

class PlanningFlow(BaseFlow):
    """
    A flow that manages planning and execution of tasks using agents.
    It breaks down a complex request into a plan and executes it step-by-step.
    """

    def __init__(self, primary_agent: Agent, planning_tool: Optional[PlanningTool] = None):
        super().__init__(primary_agent)
        self.planning_tool = planning_tool or PlanningTool()
        self.active_plan_id = f"plan_{int(time.time())}"
        self.current_step_index: Optional[int] = None

    async def execute(self, input_text: str) -> str:
        """Execute the planning flow."""
        try:
            # 1. Create Initial Plan
            await self._create_initial_plan(input_text)

            if self.active_plan_id not in self.planning_tool.plans:
                return f"Failed to create plan for: {input_text}"

            result_summary = ""

            # 2. Execution Loop
            while True:
                # Identify next step
                step_index, step_info = self._get_next_step()

                if step_index is None:
                    # No more steps to execute
                    break

                self.current_step_index = step_index
                step_text = step_info.get("text", "")
                logger.info(f"Executing Step {step_index}: {step_text}")

                # Execute step
                step_result = await self._execute_step(self.primary_agent, step_index, step_text)
                result_summary += f"\nStep {step_index} Result: {step_result}\n"

                # Mark completed
                self._mark_step_completed(step_index)

            # 3. Finalize
            return await self._finalize_plan(result_summary)

        except Exception as e:
            logger.error(f"PlanningFlow execution failed: {e}")
            return f"Error executing plan: {e}"

    async def _create_initial_plan(self, request: str):
        """Generates the initial plan using the Agent's LLM."""
        system_prompt = (
            "You are a planning assistant. Create a concise, actionable plan with clear steps "
            "to accomplish the user's request. Focus on key milestones. "
            "Use the 'planning' tool to create the plan."
        )

        # We temporarily use the agent's LLM to generate the plan structure
        # Construct messages manually for the LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a plan for: {request}"}
        ]

        # We need the planning tool schema
        tools = [self.planning_tool.to_schema()]

        # Call LLM
        response = await self._llm_call(messages, tools)

        # Process tool calls to create the plan
        if response.tool_calls:
            for tool_call in response.tool_calls:
                # Handle both object and dict access for tool_call
                func_name = tool_call.function.name if hasattr(tool_call, 'function') else tool_call['function']['name']

                if func_name == "planning":
                    if hasattr(tool_call, 'function'):
                        args_str = tool_call.function.arguments
                    else:
                        args_str = tool_call['function']['arguments']

                    args = json.loads(args_str)
                    args["plan_id"] = self.active_plan_id # Force ID consistency
                    await self._tool_execute(args)
                    return

        # Fallback: Create default plan if LLM didn't call tool
        logger.warning("LLM did not call planning tool. Creating default plan.")
        self.planning_tool.execute(
            command="create",
            plan_id=self.active_plan_id,
            title="Auto-generated Plan",
            steps=[request] # Treat whole request as one step
        )

    def _get_next_step(self) -> tuple[Optional[int], Optional[Dict]]:
        """Finds the next 'not_started' step."""
        if self.active_plan_id not in self.planning_tool.plans:
            return None, None

        plan = self.planning_tool.plans[self.active_plan_id]
        steps = plan.get("steps", [])
        statuses = plan.get("step_statuses", [])

        for i, status in enumerate(statuses):
            if status == "not_started":
                # Mark in progress
                self.planning_tool.execute(
                    command="mark_step",
                    plan_id=self.active_plan_id,
                    step_index=i,
                    step_status="in_progress"
                )
                return i, {"text": steps[i]}

        return None, None

    async def _execute_step(self, agent: Agent, step_index: int, step_text: str) -> str:
        """Delegates the step execution to the agent."""
        plan_context = self.planning_tool.execute("get", plan_id=self.active_plan_id)

        prompt = f"""
        You are executing a step in a larger plan.

        CURRENT PLAN STATUS:
        {plan_context}

        YOUR CURRENT TASK (Step {step_index}):
        "{step_text}"

        Execute this step using your tools. When finished, provide a summary of your work.
        """

        # Run the agent autonomously on this sub-task
        # Note: We might want to limit the steps for a sub-task or use a fresh memory context
        # For now, we reuse the agent's memory but inject this specific prompt.
        return await agent.run(prompt)

    def _mark_step_completed(self, step_index: int):
        self.planning_tool.execute(
            command="mark_step",
            plan_id=self.active_plan_id,
            step_index=step_index,
            step_status="completed"
        )

    async def _finalize_plan(self, result_summary: str) -> str:
        plan_text = self.planning_tool.execute("get", plan_id=self.active_plan_id)
        return f"Plan Execution Completed.\n\nSummary:\n{result_summary}\n\nFinal Plan Status:\n{plan_text}"

    async def _llm_call(self, messages: List[Dict], tools: List[Dict]) -> Message:
        """Helper to call the agent's LLM provider directly."""
        import asyncio
        return await asyncio.to_thread(
            self.primary_agent.llm.chat,
            history=messages,
            tools=tools,
            tool_choice="auto"
        )

    async def _tool_execute(self, args: Dict):
        """Helper to execute planning tool async."""
        import asyncio
        # Planning tool execute is synchronous in our port, but we wrap it for consistency
        return self.planning_tool.execute(**args)
