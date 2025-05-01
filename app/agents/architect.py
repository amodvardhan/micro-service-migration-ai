from typing import Dict, Any, List
from app.core.llm_service import LLMService
from pydantic import BaseModel, Field, ValidationError
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommunicationPattern(BaseModel):
    source: str
    target: str
    type: str
    purpose: str

class ServiceBoundary(BaseModel):
    name: str
    description: str
    responsibilities: List[str]
    entities: List[str]
    apis: List[str]
    files: List[str]

class BoundaryDetectionOutput(BaseModel):
    service_boundaries: List[ServiceBoundary]
    rationale: str
    communication_patterns: List[CommunicationPattern]

class ArchitectAgent:
    """Agent for architectural analysis and service boundary identification"""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def identify_service_boundaries(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._prepare_boundary_detection_prompt(analysis_results)
        prompt += (
            "\n\n"
            "Return your answer as a valid JSON object matching this schema:\n"
            "{\n"
            "  \"service_boundaries\": [\n"
            "    {\"name\": string, \"description\": string, \"responsibilities\": [string], \"entities\": [string], \"apis\": [string], \"files\": [string]}\n"
            "  ],\n"
            "  \"rationale\": string,\n"
            "  \"communication_patterns\": [\n"
            "    {\"source\": string, \"target\": string, \"type\": string, \"purpose\": string}\n"
            "  ]\n"
            "}\n"
        )

        boundaries_response = await self.llm_service.generate_completion(prompt)
        try:
            content = boundaries_response.get("content", "")
            json_start = content.find("{")
            json_str = content[json_start:]
            llm_json = json.loads(json_str)
            parsed = BoundaryDetectionOutput.parse_obj(llm_json)
            return parsed.dict()
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}\nRaw content:\n{content}")
            return {
                "service_boundaries": [],
                "rationale": "Parsing failed. See logs.",
                "communication_patterns": []
            }

    def _prepare_boundary_detection_prompt(self, analysis_results: Dict[str, Any]) -> str:
        prompt = "Based on the following code analysis, identify logical microservice boundaries.\n"
        prompt += "Entities:\n"
        for entity in analysis_results.get("entities", []):
            prompt += f"- {entity.get('name')} ({entity.get('type', 'class')})\n"
        prompt += "API Endpoints:\n"
        for endpoint in analysis_results.get("api_endpoints", []):
            prompt += f"- {endpoint.get('route', '')}\n"
        prompt += "Potential Services:\n"
        for svc in analysis_results.get("potential_services", []):
            prompt += f"- {svc.get('name')}\n"
        prompt += (
            "\nReturn your answer as a valid JSON object matching this schema:\n"
            "{\n"
            "  \"service_boundaries\": [ ... ],\n"
            "  \"rationale\": string,\n"
            "  \"communication_patterns\": [ ... ]\n"
            "}\n"
            "Do NOT return an empty list unless there are truly no possible boundaries."
        )
        return prompt

