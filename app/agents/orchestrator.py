# app/orchestrator.py
from typing import Dict, List, Any, Optional, Callable
import logging
import asyncio

logger = logging.getLogger(__name__)

class Task:
    def __init__(self, agent: str, action: str, params: Dict[str, Any]):
        self.agent = agent
        self.action = action
        self.params = params
        self.id = f"{agent}_{action}_{id(self)}"

class TaskQueue:
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task) -> None:
        logger.debug(f"Adding task to queue: {task.id}")
        self.tasks.append(task)

    def get_next_task(self) -> Optional[Task]:
        if self.tasks:
            task = self.tasks.pop(0)
            logger.debug(f"Retrieved task from queue: {task.id}")
            return task
        logger.debug("No tasks left in queue.")
        return None

    def is_empty(self) -> bool:
        return len(self.tasks) == 0

class AgentOrchestrator:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.agents: Dict[str, Any] = {}
        self.task_queue = TaskQueue()

    def register_agent(self, name: str, agent: Any) -> None:
        logger.info(f"Registering agent: {name}")
        self.agents[name] = agent

    async def process_codebase(self, repo_url: str) -> Dict[str, Any]:
        logger.info(f"Starting codebase processing for repo: {repo_url}")
        initial_task = Task(
            agent='analyzer',
            action='analyze_repository',
            params={'repo_url': repo_url}
        )
        self.task_queue.add_task(initial_task)
        results: Dict[str, Any] = {}
        parsed_files: Dict[str, Any] = {}

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

                # Save parsed_files from analyzer for use in developer tasks
                if current_task.agent == 'analyzer' and 'parsed_files' in result:
                    parsed_files = result['parsed_files']

            except Exception as e:
                logger.error(f"Error executing task {current_task.id}: {str(e)}")
                results[current_task.id] = {"error": str(e)}
                continue

            # Generate follow-up tasks based on result
            follow_up_tasks = self._generate_follow_up_tasks(current_task, result, parsed_files)
            for task in follow_up_tasks:
                self.task_queue.add_task(task)

        # Validate complete file coverage after all tasks
        self._validate_complete_coverage(results, parsed_files)
        
        logger.info(f"Codebase processing complete for repo: {repo_url}")
        return results

    def _generate_follow_up_tasks(self, task: Task, result: Dict[str, Any], parsed_files: Dict[str, Any]) -> List[Task]:
        follow_up_tasks: List[Task] = []

        if task.agent == 'analyzer' and task.action == 'analyze_repository':
            follow_up_tasks.append(Task(
                agent='architect',
                action='identify_service_boundaries',
                params={'analysis_results': result}
            ))

        elif task.agent == 'architect' and task.action == 'identify_service_boundaries':
            analysis_results = result.get('analysis_results', result)
            service_list = analysis_results.get('service_boundaries') or analysis_results.get('potential_services', [])
            
            # Ensure complete file mapping before creating developer tasks
            service_list = self._ensure_complete_file_mapping(service_list, parsed_files)
            
            for service in service_list:
                files_for_service = {
                    f: parsed_files[f]
                    for f in service.get("files", [])
                    if f in parsed_files
                }
                
                # Only create developer task if service has files
                if files_for_service:
                    follow_up_tasks.append(Task(
                        agent='developer',
                        action='refactor_code',
                        params={
                            'service_boundary': service,
                            'original_code': files_for_service
                        }
                    ))
                else:
                    logger.warning(f"Service '{service.get('name')}' has no files mapped to it")

        return follow_up_tasks

    def _ensure_complete_file_mapping(self, service_list: List[Dict], parsed_files: Dict[str, Any]) -> List[Dict]:
        """Ensure every file is mapped to a service"""
        all_service_files = set()
        for service in service_list:
            all_service_files.update(service.get("files", []))
        
        unassigned_files = set(parsed_files.keys()) - all_service_files
        if unassigned_files:
            # Create a shared/unassigned service for unmapped files
            shared_service = {
                "name": "SharedOrUnassigned",
                "description": "Files not mapped to any specific service",
                "responsibilities": ["Shared utilities", "Configuration files", "Build scripts"],
                "entities": [],
                "apis": [],
                "files": list(unassigned_files)
            }
            service_list.append(shared_service)
            logger.warning(f"{len(unassigned_files)} files were not mapped to any service. Assigning to 'SharedOrUnassigned'.")
        
        return service_list

    def _validate_complete_coverage(self, results: Dict[str, Any], parsed_files: Dict[str, Any]):
        """Validate that all files were processed by developer agents"""
        developer_outputs = [
            v for k, v in results.items() 
            if k.startswith("developer_refactor_code") and isinstance(v, dict) and "files" in v
        ]
        
        if not developer_outputs:
            logger.error("No developer outputs found - no code was generated")
            return
        
        # Count files in developer outputs
        all_generated_files = set()
        total_generated_files = 0
        
        for dev_output in developer_outputs:
            service_name = dev_output.get("service_name", "Unknown")
            files = dev_output.get("files", [])
            
            if not files or (len(files) == 1 and files[0].get("path") == "README.txt"):
                logger.warning(f"Service '{service_name}' only generated README.txt - no actual code generated")
            else:
                for f in files:
                    if isinstance(f, dict) and "path" in f:
                        all_generated_files.add(f["path"])
                        total_generated_files += 1
                logger.info(f"Service '{service_name}' generated {len(files)} files")
        
        logger.info(f"Total files in repository: {len(parsed_files)}")
        logger.info(f"Total generated files across all services: {total_generated_files}")
        logger.info(f"Unique generated file paths: {len(all_generated_files)}")
        
        # Check for services that failed to generate code
        failed_services = []
        successful_services = []
        
        for dev_output in developer_outputs:
            service_name = dev_output.get("service_name", "Unknown")
            files = dev_output.get("files", [])
            
            if not files or (len(files) == 1 and files[0].get("path") in ["README.txt", "README.md"] and 
                           "Error generating code" in files[0].get("content", "")):
                failed_services.append(service_name)
            else:
                successful_services.append(service_name)
        
        if failed_services:
            logger.error(f"Services that failed to generate code: {failed_services}")
        
        if successful_services:
            logger.info(f"Services that successfully generated code: {successful_services}")
        else:
            logger.error("No services successfully generated code - check DeveloperAgent implementation")

    async def get_processing_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of the processing results"""
        summary = {
            "total_tasks": len(results),
            "successful_tasks": 0,
            "failed_tasks": 0,
            "services_identified": 0,
            "services_with_code": 0,
            "services_failed": 0,
            "task_breakdown": {}
        }
        
        for task_id, result in results.items():
            agent_name = task_id.split('_')[0]
            
            if agent_name not in summary["task_breakdown"]:
                summary["task_breakdown"][agent_name] = {"success": 0, "failed": 0}
            
            if isinstance(result, dict) and "error" in result:
                summary["failed_tasks"] += 1
                summary["task_breakdown"][agent_name]["failed"] += 1
            else:
                summary["successful_tasks"] += 1
                summary["task_breakdown"][agent_name]["success"] += 1
                
                # Count services
                if agent_name == "architect":
                    service_boundaries = result.get("service_boundaries", [])
                    summary["services_identified"] = len(service_boundaries)
                
                elif agent_name == "developer":
                    files = result.get("files", [])
                    if files and not (len(files) == 1 and files[0].get("path") == "README.txt"):
                        summary["services_with_code"] += 1
                    else:
                        summary["services_failed"] += 1
        
        return summary
