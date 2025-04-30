import os
import tempfile
import git
from typing import Dict, Any, List
import glob
import logging
import json
from pydantic import BaseModel, ValidationError, Field

from app.core.llm_service import LLMService
from app.knowledge.embedding_manager import EmbeddingManager
from app.core.code_analyzer import CodeAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeParser:
    async def clone_repository(self, repo_url: str) -> str:
        try:
            temp_dir = tempfile.mkdtemp()
            git.Repo.clone_from(repo_url, temp_dir)
            return temp_dir
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            raise

    async def parse_directory(self, directory_path: str) -> Dict[str, Any]:
        parsed_files = {}
        code_files = self._find_code_files(directory_path)
        for file_path in code_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                relative_path = os.path.relpath(file_path, directory_path)
                parsed_files[relative_path] = {
                    'content': content,
                    'extension': os.path.splitext(file_path)[1],
                    'size': os.path.getsize(file_path)
                }
            except Exception as e:
                logger.error(f"Error parsing file {file_path}: {str(e)}")
        return parsed_files

    def _find_code_files(self, directory_path: str) -> List[str]:
        extensions = [
            '.cs', '.csproj', '.sln', '.py', '.js', '.ts', '.java', '.go',
            '.xml', '.json', '.yaml', '.yml'
        ]
        code_files = []
        for ext in extensions:
            pattern = os.path.join(directory_path, '**', f'*{ext}')
            code_files.extend(glob.glob(pattern, recursive=True))
        return code_files

class PotentialService(BaseModel):
    name: str
    entities: List[str]
    responsibilities: List[str]

class LLMAnalysisOutput(BaseModel):
    architecture_type: str
    architecture_insights: Dict[str, Any]
    potential_services: List[PotentialService]

class CodeAnalysisAgent:
    def __init__(self, llm_service: LLMService, embedding_manager: EmbeddingManager):
        self.llm_service = llm_service
        self.embedding_manager = embedding_manager
        self.code_parser = CodeParser()
        self.code_analyzer = CodeAnalyzer()

    async def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        try:
            logger.info(f"Cloning repository: {repo_url}")
            repo_path = await self.code_parser.clone_repository(repo_url)
            logger.info(f"Parsing code files from repository")
            parsed_files = await self.code_parser.parse_directory(repo_path)
            logger.info(f"Found {len(parsed_files)} files in repository")

            logger.info("Generating and storing embeddings for code files")
            embedding_results = await self.embedding_manager.process_codebase(parsed_files)
            logger.info(f"Processed {embedding_results['processed_files']} files for embeddings")

            logger.info("Performing static code analysis")
            static_analysis = await self.code_analyzer.analyze_codebase(parsed_files)
            logger.info(f"Identified {len(static_analysis.get('entities', []))} entities and {len(static_analysis.get('potential_services', []))} potential services")

            sample_files = self._select_representative_files(parsed_files)
            logger.info("Analyzing code structure and dependencies with LLM")
            llm_analysis = await self._analyze_with_llm(sample_files, static_analysis)

            # --- Merge static and LLM results robustly ---
            analysis_results = self._combine_analysis_results(static_analysis, llm_analysis)

            if embedding_results["processed_files"] > 0:
                logger.info("Enhancing analysis with semantic similarity insights")
                semantic_insights = await self._generate_semantic_insights(parsed_files, embedding_results)
                analysis_results["semantic_insights"] = semantic_insights

            logger.info("Repository analysis completed successfully")
            return {
                'repo_path': repo_path,
                'parsed_files': parsed_files,
                'embedding_results': embedding_results,
                'analysis_results': analysis_results
            }
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            raise

    async def _generate_semantic_insights(self, parsed_files: Dict[str, Any], embedding_results: Dict[str, Any]) -> Dict[str, Any]:
        return {"similar_file_groups": [], "potential_boundaries": [], "duplication_candidates": []}

    def _combine_analysis_results(self, static_analysis: Dict[str, Any], llm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        # Only accept LLM services that match actual namespaces/entities
        valid_namespaces = set(static_analysis.get("namespaces", {}).keys())
        valid_entities = set(e["name"] for e in static_analysis.get("entities", []))
        filtered_services = []
        for svc in llm_analysis.get("potential_services", []):
            svc_entities = set(svc.get("entities", []))
            if svc_entities & valid_entities:
                filtered_services.append(svc)
        # If no valid services, fallback to static analysis
        if not filtered_services:
            filtered_services = static_analysis.get("potential_services", [])
        combined = dict(static_analysis)
        combined["potential_services"] = filtered_services
        combined["architecture_type"] = llm_analysis.get("architecture_type") or static_analysis.get("architecture_type", "Unknown")
        combined["architecture_insights"] = llm_analysis.get("architecture_insights", {})
        combined["entities"] = static_analysis.get("entities", [])
        combined["api_endpoints"] = static_analysis.get("api_endpoints", [])
        combined["dependencies"] = static_analysis.get("dependencies", [])
        return combined


    async def _analyze_with_llm(self, sample_files: Dict[str, Any], static_analysis: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._prepare_analysis_prompt(sample_files, static_analysis)
        prompt += (
            "\n\n"
            "Return your answer as a valid JSON object matching this schema:\n"
            "{\n"
            "  \"architecture_type\": string,\n"
            "  \"architecture_insights\": object,\n"
            "  \"potential_services\": [\n"
            "    {\"name\": string, \"entities\": [string], \"responsibilities\": [string]}\n"
            "  ]\n"
            "}\n"
        )
        analysis_response = await self.llm_service.generate_completion(prompt)
        content = analysis_response.get("content", "")
        try:
            json_start = content.find("{")
            json_str = content[json_start:]
            llm_json = json.loads(json_str)
            parsed = LLMAnalysisOutput.parse_obj(llm_json)
            return parsed.dict()
        except (json.JSONDecodeError, ValidationError, Exception) as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}\nRaw content:\n{content}")
            return {
                "architecture_type": "Unknown",
                "architecture_insights": {},
                "potential_services": []
            }

    def _prepare_analysis_prompt(self, sample_files: Dict[str, Any], static_analysis: Dict[str, Any]) -> str:
        prompt = (
            "You are an expert in software architecture and code analysis.\n"
            "Analyze the following codebase and static analysis results to identify potential microservice boundaries.\n"
            "You MUST only propose services that are grounded in the actual namespaces and entities found below.\n\n"
            "## Namespaces and Entities Found:\n"
        )
        # List namespaces and their entities
        for ns, files in static_analysis.get("namespaces", {}).items():
            ns_entities = [e["name"] for e in static_analysis.get("entities", []) if e.get("namespace") == ns]
            if ns_entities:
                prompt += f"- Namespace: {ns}\n  Entities: {', '.join(ns_entities)}\n"
        prompt += "\n## API Endpoints Found:\n"
        for ep in static_analysis.get("api_endpoints", []):
            prompt += f"- {ep.get('method', 'GET')} {ep.get('route', '')}\n"
        prompt += "\n## Sample Code Files:\n"
        for file_path, file_info in list(sample_files.items())[:3]:
            prompt += f"File: {file_path}\n"
            prompt += "```\n"
            content = file_info.get('content', '')
            if len(content) > 1000:
                content = content[:1000] + "...[truncated]"
            prompt += content + "\n```\n\n"
        prompt += (
            "Based ONLY on the above namespaces and entities, return a JSON object with this schema:\n"
            "{\n"
            "  \"architecture_type\": string,\n"
            "  \"architecture_insights\": object,\n"
            "  \"potential_services\": [\n"
            "    {\"name\": string, \"entities\": [string], \"responsibilities\": [string]}\n"
            "  ]\n"
            "}\n"
            "Do NOT invent services unrelated to the namespaces/entities above. If you cannot identify any, return an empty list."
        )
        return prompt

    def _select_representative_files(self, parsed_files: Dict[str, Any], sample_size: int = 3) -> Dict[str, Any]:
        sorted_files = sorted(parsed_files.items(), key=lambda x: x[1]['size'], reverse=True)
        return dict(sorted_files[:sample_size])
