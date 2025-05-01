from typing import Dict, Any, List
from app.core.llm_service import LLMService
from pydantic import BaseModel, ValidationError
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeneratedFile(BaseModel):
    path: str
    content: str

class RefactoredServiceCode(BaseModel):
    service_name: str
    files: List[GeneratedFile]

class CodeGenerator:
    def optimize(self, code: Dict[str, Any]) -> Dict[str, Any]:
        return code

class DeveloperAgent:
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.code_generator = CodeGenerator()

    async def refactor_code(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Refactoring code for service: {service_boundary.get('name')}, files: {len(original_code)}")
        # If the service boundary's files list is empty, fallback to all files (for debugging)
        if not original_code:
            logger.warning("No files passed to DeveloperAgent; using all parsed files for debugging.")
            # This requires you to pass parsed_files as a backup param if needed
            # original_code = parsed_files

        prompt = self._prepare_refactoring_prompt(service_boundary, original_code)
        prompt += (
            "\n\nReturn your answer as a valid JSON object matching this schema:\n"
            "{\n"
            "  \"service_name\": string,\n"
            "  \"files\": [\n"
            "    {\"path\": string, \"content\": string}\n"
            "  ]\n"
            "}\n"
            "For each file, provide a realistic filename and the full code content. "
            "Include controllers, models, services, data layer, Dockerfile, and README. "
            "If you cannot generate code, return at least one file with a README and explanation."
        )

        try:
            llm_response = await self.llm_service.generate_completion(prompt)
            content = llm_response.get("content", "")
            logger.info(f"DeveloperAgent LLM output: {content[:500]}...")  # Log first 500 chars
            json_start = content.find("{")
            json_str = content[json_start:]
            llm_json = json.loads(json_str)
            # Validate: must have files with content
            if "files" in llm_json and all("content" in f for f in llm_json["files"]):
                parsed = RefactoredServiceCode.parse_obj(llm_json)
                optimized_code = self.code_generator.optimize(parsed.dict())
                return optimized_code
            else:
                logger.warning("LLM output missing 'files' or file content.")
                return {
                    "service_name": service_boundary.get("name"),
                    "files": [
                        {"path": "README.txt", "content": "No code generated."}
                    ]
                }
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}\nRaw content:\n{content if 'content' in locals() else ''}")
            return {
                'service_name': service_boundary['name'],
                'files': [
                    {"path": "README.txt", "content": "Error generating code."}
                ]
            }

    def _prepare_refactoring_prompt(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> str:
        prompt = f"Refactor the following code to create a microservice for '{service_boundary['name']}'.\n\n"
        prompt += f"Service Name: {service_boundary['name']}\n"
        prompt += f"Description: {service_boundary.get('description', 'N/A')}\n"
        prompt += f"Responsibilities: {', '.join(service_boundary.get('responsibilities', []))}\n"
        prompt += f"Entities: {', '.join(service_boundary.get('entities', []))}\n"
        prompt += f"APIs: {', '.join(service_boundary.get('apis', []))}\n\n"
        prompt += "Original Code:\n"
        for file_path, file_info in original_code.items():
            prompt += f"File: {file_path}\n"
            prompt += "```\n"
            content = file_info.get('content', '')
            if len(content) > 2000:
                content = content[:2000] + "...[truncated]"
            prompt += content + "\n```\n\n"
        prompt += (
            "Please refactor this code to create a microservice with the following:\n"
            "1. Controllers for the API endpoints\n"
            "2. Models for the core entities\n"
            "3. Services for the business logic\n"
            "4. Data access layer\n"
            "5. Dockerfile for containerization\n"
            "6. README file explaining the microservice\n"
            "For each file, provide a valid path and full code content. "
            "Return your answer as JSON as described above."
        )
        return prompt
