from typing import Dict, List, Any, Optional, Callable
from app.core.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

class Task:
    """Represents a task to be executed by an agent"""

    def __init__(self, agent: str, action: str, params: Dict[str, Any]):
        self.agent = agent
        self.action = action
        self.params = params
        self.id = f"{agent}_{action}_{id(self)}"

class TaskQueue:
    """A simple FIFO queue for managing tasks"""

    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to the queue"""
        logger.debug(f"Adding task to queue: {task.id}")
        self.tasks.append(task)

    def get_next_task(self) -> Optional[Task]:
        """Get the next task from the queue"""
        if self.tasks:
            task = self.tasks.pop(0)
            logger.debug(f"Retrieved task from queue: {task.id}")
            return task
        logger.debug("No tasks left in queue.")
        return None

    def is_empty(self) -> bool:
        """Check if the queue is empty"""
        return len(self.tasks) == 0

class AgentOrchestrator:
    """Coordinates the activities of multiple AI agents"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.agents: Dict[str, Any] = {}
        self.task_queue = TaskQueue()

    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent with the orchestrator"""
        logger.info(f"Registering agent: {name}")
        self.agents[name] = agent

    async def process_codebase(self, repo_url: str) -> Dict[str, Any]:
        """
        Process a codebase from the given repository URL.
        Returns a dictionary of all results keyed by task ID.
        """
        logger.info(f"Starting codebase processing for repo: {repo_url}")
        initial_task = Task(
            agent='analyzer',
            action='analyze_repository',
            params={'repo_url': repo_url}
        )
        self.task_queue.add_task(initial_task)
        results: Dict[str, Any] = {}

        while not self.task_queue.is_empty():
            current_task = self.task_queue.get_next_task()
            if not current_task:
                continue

            agent = self.agents.get(current_task.agent)
            if not agent:
                logger.error(f"Agent '{current_task.agent}' not found. Skipping task {current_task.id}.")
                continue

            action_fn: Optional[Callable] = getattr(agent, current_task.action, None)
            if not action_fn:
                logger.error(f"Action '{current_task.action}' not found in agent '{current_task.agent}'. Skipping task {current_task.id}.")
                continue

            try:
                logger.info(f"Executing task {current_task.id} ({current_task.agent}.{current_task.action})")
                result = await action_fn(**current_task.params)
                results[current_task.id] = result
            except Exception as e:
                logger.error(f"Error executing task {current_task.id}: {str(e)}")
                results[current_task.id] = {"error": str(e)}
                continue

            # Generate follow-up tasks based on result
            follow_up_tasks = self._generate_follow_up_tasks(current_task, result)
            for task in follow_up_tasks:
                self.task_queue.add_task(task)

        logger.info(f"Codebase processing complete for repo: {repo_url}")
        return results

    def _generate_follow_up_tasks(self, task: Task, result: Dict[str, Any]) -> List[Task]:
        """
        Generate follow-up tasks based on the current task and its result.
        Extend this method to add more dynamic or configurable task flows.
        """
        follow_up_tasks: List[Task] = []

        if task.agent == 'analyzer' and task.action == 'analyze_repository':
            # After analysis, identify service boundaries
            follow_up_tasks.append(Task(
                agent='architect',
                action='identify_service_boundaries',
                params={'analysis_results': result}
            ))

        elif task.agent == 'architect' and task.action == 'identify_service_boundaries':
            # After identifying boundaries, refactor code for each service
            analysis_results = result.get('analysis_results', result)
            for service in analysis_results.get('service_boundaries', []):
                follow_up_tasks.append(Task(
                    agent='developer',
                    action='refactor_code',
                    params={
                        'service_boundary': service,
                        'original_code': analysis_results.get('parsed_files', {})
                    }
                ))

        # Future: Add more dynamic branching here as needed

        return follow_up_tasks
