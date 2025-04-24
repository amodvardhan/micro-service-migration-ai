from typing import Dict, Any, List
from app.core.llm_service import LLMService

class CodeGenerator:
    """Generates and optimizes code for microservices"""
    
    def optimize(self, code: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize the generated code"""
        # This is a placeholder - in a real implementation,
        # you would have more sophisticated optimization logic
        return code

class DeveloperAgent:
    """Agent for refactoring and generating microservice code"""
    
    def __init__(self, llm_service: LLMService):
        """Initialize the agent with the LLM service"""
        self.llm_service = llm_service
        self.code_generator = CodeGenerator()
        
    async def refactor_code(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code for a specific microservice"""
        # Prepare prompt for code refactoring
        prompt = self._prepare_refactoring_prompt(service_boundary, original_code)
        
        # Get refactored code from LLM
        # Note: This is commented out to avoid making API calls during setup
        # refactored_code = await self.llm_service.generate_completion(prompt)
        
        # For now, return a placeholder
        refactored_code = {
            'service_name': service_boundary['name'],
            'files': [
                {
                    'path': f"{service_boundary['name']}/Controllers/{service_boundary['name']}Controller.cs",
                    'content': f"// Controller for {service_boundary['name']}\n// This is a placeholder"
                },
                {
                    'path': f"{service_boundary['name']}/Models/{service_boundary['name']}Model.cs",
                    'content': f"// Model for {service_boundary['name']}\n// This is a placeholder"
                },
                {
                    'path': f"{service_boundary['name']}/Services/{service_boundary['name']}Service.cs",
                    'content': f"// Service for {service_boundary['name']}\n// This is a placeholder"
                }
            ]
        }
        
        # Post-process and optimize the generated code
        optimized_code = self.code_generator.optimize(refactored_code)
        
        return optimized_code
        
    def _prepare_refactoring_prompt(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> str:
        """Prepare a prompt for code refactoring"""
        prompt = f"Refactor the following code to create a microservice for '{service_boundary['name']}'.\n\n"
        
        # Add service boundary details
        prompt += f"Service Name: {service_boundary['name']}\n"
        prompt += f"Description: {service_boundary.get('description', 'N/A')}\n"
        prompt += f"Responsibilities: {', '.join(service_boundary.get('responsibilities', []))}\n"
        prompt += f"Entities: {', '.join(service_boundary.get('entities', []))}\n"
        prompt += f"APIs: {', '.join(service_boundary.get('apis', []))}\n\n"
        
        # Add relevant original code
        # This is a simplified version - in a real implementation,
        # you would have more sophisticated code selection logic
        prompt += "Original Code:\n"
        for file_path, file_info in list(original_code.items())[:3]:  # Take up to 3 files
            prompt += f"File: {file_path}\n"
            prompt += f"```\n"
            
            # Limit content length to avoid token limits
            content = file_info.get('content', '')
            if len(content) > 1000:
                content = content[:1000] + "...[truncated]"
                
            prompt += content + "\n```\n\n"
            
        prompt += "Please refactor this code to create a microservice with the following:\n"
        prompt += "1. Controllers for the API endpoints\n"
        prompt += "2. Models for the core entities\n"
        prompt += "3. Services for the business logic\n"
        prompt += "4. Data access layer\n"
        prompt += "5. Dockerfile for containerization\n"
        
        return prompt