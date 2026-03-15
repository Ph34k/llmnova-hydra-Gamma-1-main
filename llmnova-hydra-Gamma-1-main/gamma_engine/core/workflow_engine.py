
from typing import Dict, List, Any, Callable, Optional, Set
import json
import os
import networkx as nx
from gamma_engine.core.scheduler import TaskScheduler
from gamma_engine.core.logger import logger

class WorkflowEngine:
    def __init__(self, scheduler: TaskScheduler, persistence_path: str = "workflow_state.json"):
        self.scheduler = scheduler
        self.persistence_path = persistence_path
        self.workflows: Dict[str, nx.DiGraph] = {}  # Store workflows as DAGs
        self.active_contexts: Dict[str, Dict[str, Any]] = {}

    def register_workflow(self, name: str, steps: List[Dict[str, Any]]):
        """
        Registers a DAG workflow.

        Args:
            name: Workflow identifier.
            steps: List of dicts defining steps and dependencies.
                   Example: [{'id': 'step1', 'func': func1},
                             {'id': 'step2', 'func': func2, 'depends_on': ['step1']}]
        """
        graph = nx.DiGraph()
        for step in steps:
            step_id = step['id']
            func = step['func']
            graph.add_node(step_id, func=func, status="pending")

            dependencies = step.get('depends_on', [])
            for dep in dependencies:
                graph.add_edge(dep, step_id)

        if not nx.is_directed_acyclic_graph(graph):
            raise ValueError(f"Workflow '{name}' contains cycles.")

        self.workflows[name] = graph
        logger.info(f"Registered DAG workflow: {name}")

    def execute_workflow(self, name: str, context: Dict[str, Any]) -> str:
        """
        Starts execution of a DAG workflow.
        Returns execution ID.
        """
        if name not in self.workflows:
            logger.error(f"Workflow '{name}' not found.")
            return None

        import uuid
        exec_id = str(uuid.uuid4())

        # Clone the graph for this execution instance
        self.active_contexts[exec_id] = {
            "workflow_name": name,
            "graph": self.workflows[name].copy(),
            "data": context,
            "status": "running"
        }

        logger.info(f"Started workflow execution {exec_id} for '{name}'")
        self._process_graph(exec_id)
        return exec_id

    def _process_graph(self, exec_id: str):
        context = self.active_contexts.get(exec_id)
        if not context:
            return

        graph = context['graph']
        data = context['data']

        # Find nodes with 0 in-degree (no pending dependencies) and not yet completed
        pending_nodes = [n for n, attr in graph.nodes(data=True) if attr['status'] == 'pending']

        if not pending_nodes:
            # Check if all completed
            if all(attr['status'] == 'completed' for n, attr in graph.nodes(data=True)):
                context['status'] = 'completed'
                self._save_state()
                logger.info(f"Workflow {exec_id} completed successfully.")
            return

        progress_made = False
        for node in pending_nodes:
            # Check dependencies
            predecessors = list(graph.predecessors(node))
            if all(graph.nodes[p]['status'] == 'completed' for p in predecessors):
                # Execute Node
                try:
                    func = graph.nodes[node]['func']
                    logger.info(f"Executing step '{node}' in workflow {exec_id}...")

                    # Function updates 'data' dict in place or returns new dict
                    result = func(data)
                    if isinstance(result, dict):
                        data.update(result)

                    graph.nodes[node]['status'] = 'completed'
                    progress_made = True
                except Exception as e:
                    logger.error(f"Step '{node}' failed: {e}")
                    graph.nodes[node]['status'] = 'failed'
                    context['status'] = 'failed'
                    self._save_state()
                    return

        if progress_made:
            # Recursively process next steps
            self._process_graph(exec_id)

        self._save_state()

    def _save_state(self):
        """Persist minimal state (IDs and status) to disk."""
        try:
            state = {}
            for eid, ctx in self.active_contexts.items():
                state[eid] = {
                    "workflow": ctx["workflow_name"],
                    "status": ctx["status"],
                    "data": ctx["data"]
                    # Graph state serialization is complex, skipping for MVP
                }
            with open(self.persistence_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")

    def load_state(self):
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r") as f:
                    state = json.load(f)
                    # Rehydration logic would go here
                    logger.info(f"Loaded {len(state)} workflow states.")
            except Exception as e:
                logger.error(f"Failed to load workflow state: {e}")
