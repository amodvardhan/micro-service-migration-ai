from typing import Dict, Any, List
from app.core.llm_service import LLMService
from pydantic import BaseModel, ValidationError
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Define the expected LLM output schema ---

class GeneratedFile(BaseModel):
    path: str
    content: str

class RefactoredServiceCode(BaseModel):
    service_name: str
    files: List[GeneratedFile]

class CodeGenerator:
    """Generates and optimizes code for microservices"""
    def optimize(self, code: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for future sophisticated optimization logic
        return code

class DeveloperAgent:
    """Agent for refactoring and generating microservice code"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGenerator()

    async def refactor_code(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code for a specific microservice (dynamic, robust)"""
        prompt = self._prepare_refactoring_prompt(service_boundary, original_code)
        # Instruct the LLM to return a valid JSON object matching the schema
        prompt += (
            "\n\n"
            "Return your answer as a valid JSON object matching this schema:\n"
            "{\n"
            "  \"service_name\": string,\n"
            "  \"files\": [\n"
            "    {\"path\": string, \"content\": string}\n"
            "  ]\n"
            "}\n"
        )

        # Get refactored code from LLM
        llm_response = await self.llm_service.generate_completion(prompt)
        content = llm_response.get("content", "")

        # Try to extract JSON from the LLM output
        try:
            json_start = content.find("{")
            json_str = content[json_start:]
            llm_json = json.loads(json_str)
            parsed = RefactoredServiceCode.parse_obj(llm_json)
            optimized_code = self.code_generator.optimize(parsed.dict())
            return optimized_code
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}\nRaw content:\n{content}")
            # Return a safe default
            return {
                'service_name': service_boundary['name'],
                'files': []
            }

    def _prepare_refactoring_prompt(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> str:
        """Prepare a prompt for code refactoring"""
        prompt = f"Refactor the following code to create a microservice for '{service_boundary['name']}'.\n\n"
        prompt += f"Service Name: {service_boundary['name']}\n"
        prompt += f"Description: {service_boundary.get('description', 'N/A')}\n"
        prompt += f"Responsibilities: {', '.join(service_boundary.get('responsibilities', []))}\n"
        prompt += f"Entities: {', '.join(service_boundary.get('entities', []))}\n"
        prompt += f"APIs: {', '.join(service_boundary.get('apis', []))}\n\n"
        prompt += "Original Code:\n"
        for file_path, file_info in list(original_code.items())[:3]:
            prompt += f"File: {file_path}\n"
            prompt += f"```\n"
            content = file_info.get('content', '')
            if len(content) > 1000:
                content = content[:1000] + "...[truncated]"
            prompt += content + "\n```\n\n"
        prompt += (
            "Please refactor this code to create a microservice with the following:\n"
            "1. Controllers for the API endpoints\n"
            "2. Models for the core entities\n"
            "3. Services for the business logic\n"
            "4. Data access layer\n"
            "5. Dockerfile for containerization\n"
        )
        return prompt
