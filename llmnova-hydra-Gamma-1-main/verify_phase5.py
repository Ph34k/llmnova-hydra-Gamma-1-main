import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

import asyncio

from gamma_engine.core import ScheduleManager
from gamma_engine.tools import (APIGenerationTool, ComponentGenerationTool,
                                ScheduleTool, WebDevelopmentTool)


async def verify_phase5():
    print("--- Verifying Phase 5: Web Dev and Scheduling ---")
    
    # 1. Verify WebDevelopmentTool
    print("\n[1] Verifying WebDevelopmentTool...")
    web_tool = WebDevelopmentTool()
    result = web_tool.execute("generate_page", path="verify_web/index.html", title="Verification Page")
    print(f"Generate Page Result: {result}")
    
    # 2. Verify ComponentGenerationTool
    print("\n[2] Verifying ComponentGenerationTool...")
    comp_tool = ComponentGenerationTool()
    result = comp_tool.execute(name="Header", type="react", output_path="verify_web/Header.jsx", props=["title"])
    print(f"React Component Result: {result}")
    
    result = comp_tool.execute(name="Footer", type="html", output_path="verify_web/footer.html")
    print(f"HTML Component Result: {result}")
    
    # 3. Verify APIGenerationTool
    print("\n[3] Verifying APIGenerationTool...")
    api_tool = APIGenerationTool()
    result = api_tool.execute(route="/status", method="GET", output_path="verify_web/api_status.py")
    print(f"API Generation Result: {result}")
    
    # 4. Verify Scheduling
    print("\n[4] Verifying Scheduling system...")
    manager = ScheduleManager(persistence_file="verify_jobs.json")
    manager.start()
    
    sched_tool = ScheduleTool(schedule_manager=manager)
    result = sched_tool.execute("schedule", trigger_type="interval", trigger_args={"seconds": 10}, job_id="verify_job", task_description="Verification Task")
    print(f"Schedule Task Result: {result}")
    
    print("\nList of jobs:")
    print(sched_tool.execute("list"))
    
    manager.stop()
    print("\n--- Phase 5 Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify_phase5())
