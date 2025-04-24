from typing import Dict, List, Any
from app.core.llm_service import LLMService

class Task:
    """Represents a task to be executed by an agent"""
    
    def __init__(self, agent: str, action: str, params: Dict[str, Any]):
        self.agent = agent
        self.action = action
        self.params = params
        self.id = f"{agent}_{action}_{id(self)}"
        
class TaskQueue:
    """A simple queue for managing tasks"""
    
    def __init__(self):
        self.tasks = []
        
    def add_task(self, task: Task):
        """Add a task to the queue"""
        self.tasks.append(task)
        
    def get_next_task(self) -> Task:
        """Get the next task from the queue"""
        if self.tasks:
            return self.tasks.pop(0)
        return None
        
    def is_empty(self) -> bool:
        """Check if the queue is empty"""
        return len(self.tasks) == 0

class AgentOrchestrator:
    """Coordinates the activities of multiple AI agents"""
    
    def __init__(self, llm_service: LLMService):
        """Initialize the orchestrator with the LLM service"""
        self.llm_service = llm_service
        self.agents = {}  # Will be populated with agents
        self.task_queue = TaskQueue()
        
    def register_agent(self, name: str, agent):
        """Register an agent with the orchestrator"""
        self.agents[name] = agent
        
    async def process_codebase(self, repo_url: str) -> Dict[str, Any]:
        """Process a codebase from the given repository URL"""
        # Create initial analysis task
        analysis_task = Task(
            agent='analyzer',
            action='analyze_repository',
            params={'repo_url': repo_url}
        )
        self.task_queue.add_task(analysis_task)
        
        results = {}
        
        # Process tasks until completion
        while not self.task_queue.is_empty():
            current_task = self.task_queue.get_next_task()
            if not current_task:
                continue
                
            if current_task.agent not in self.agents:
                print(f"Agent {current_task.agent} not found")
                continue
                
            agent = self.agents[current_task.agent]
            if not hasattr(agent, current_task.action):
                print(f"Action {current_task.action} not found in agent {current_task.agent}")
                continue
                
            action = getattr(agent, current_task.action)
            result = await action(**current_task.params)
            
            # Store the result
            results[current_task.id] = result
            
            # Generate follow-up tasks based on the result
            follow_up_tasks = self._generate_follow_up_tasks(current_task, result)
            for task in follow_up_tasks:
                self.task_queue.add_task(task)
                
        return results
        
    def _generate_follow_up_tasks(self, task: Task, result: Dict[str, Any]) -> List[Task]:
        """Generate follow-up tasks based on the current task and its result"""
        follow_up_tasks = []
        
        # This is a simplified version - in a real implementation,
        # you would have more complex logic to determine the next steps
        if task.agent == 'analyzer' and task.action == 'analyze_repository':
            # After analysis, identify service boundaries
            follow_up_tasks.append(Task(
                agent='architect',
                action='identify_service_boundaries',
                params={'analysis_results': result}
            ))
            
        elif task.agent == 'architect' and task.action == 'identify_service_boundaries':
            # After identifying boundaries, refactor code for each service
            for service in result.get('service_boundaries', []):
                follow_up_tasks.append(Task(
                    agent='developer',
                    action='refactor_code',
                    params={
                        'service_boundary': service,
                        'original_code': result.get('analysis_results', {}).get('parsed_files', {})
                    }
                ))
                
        return follow_up_tasks
