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
    files: List[str] = Field(default_factory=list)

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

            # Use repository-specific analysis instead of generic samples
            logger.info("Analyzing code structure and dependencies with LLM using repository-specific context")
            llm_analysis = await self._analyze_with_llm(parsed_files, static_analysis)

            # Combine results and ensure every file is mapped
            analysis_results = self._combine_analysis_results(static_analysis, llm_analysis, parsed_files)

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

    def _combine_analysis_results(self, static_analysis: Dict[str, Any], llm_analysis: Dict[str, Any], parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        # Map files to services based on actual analysis
        services_with_files = []
        all_files = list(parsed_files.keys())
        
        for svc in llm_analysis.get("potential_services", []):
            # Map files to services based on entities, responsibilities, and file patterns
            service_files = self._map_files_to_service(svc, all_files, static_analysis, parsed_files)
            svc["files"] = service_files
            services_with_files.append(svc)

        # Ensure all files are mapped
        all_mapped_files = set()
        for svc in services_with_files:
            all_mapped_files.update(svc.get("files", []))
        
        unmapped_files = set(all_files) - all_mapped_files
        if unmapped_files:
            services_with_files.append({
                "name": "SharedOrUnassigned",
                "entities": [],
                "responsibilities": ["Shared utilities and unmapped files"],
                "files": list(unmapped_files)
            })
            logger.warning(f"{len(unmapped_files)} files were not mapped to any service. Assigning to 'SharedOrUnassigned'.")

        combined = dict(static_analysis)
        combined["potential_services"] = services_with_files
        combined["architecture_type"] = llm_analysis.get("architecture_type", "Monolithic")
        combined["architecture_insights"] = llm_analysis.get("architecture_insights", {})
        return combined

    def _map_files_to_service(self, service: Dict[str, Any], all_files: List[str], static_analysis: Dict[str, Any], parsed_files: Dict[str, Any]) -> List[str]:
        """Map files to services based on entities, responsibilities, and file content"""
        service_files = []
        service_entities = set(e.lower() for e in service.get("entities", []))
        service_name_parts = set(service.get("name", "").lower().split())
        service_responsibilities = set(r.lower() for r in service.get("responsibilities", []))
        
        for file_path in all_files:
            file_path_lower = file_path.lower()
            
            # Check if file relates to service entities
            if any(entity in file_path_lower for entity in service_entities):
                service_files.append(file_path)
                continue
                
            # Check if file relates to service name
            if any(part in file_path_lower for part in service_name_parts if len(part) > 3):
                service_files.append(file_path)
                continue
                
            # Check if file relates to service responsibilities
            if any(resp in file_path_lower for resp in service_responsibilities if len(resp) > 4):
                service_files.append(file_path)
                continue
                
            # Check file content for entity/responsibility references (for key files)
            if file_path.endswith(('.cs', '.py', '.java', '.js', '.ts')):
                content = parsed_files.get(file_path, {}).get('content', '').lower()
                if any(entity in content for entity in service_entities):
                    service_files.append(file_path)
                    continue
        
        return service_files

    async def _analyze_with_llm(self, parsed_files: Dict[str, Any], static_analysis: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._prepare_analysis_prompt(parsed_files, static_analysis)
        prompt += (
            "\n\nReturn your answer as a valid JSON object matching this schema:\n"
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
                "architecture_type": "Monolithic",
                "architecture_insights": {},
                "potential_services": []
            }

    def _prepare_analysis_prompt(self, parsed_files: Dict[str, Any], static_analysis: Dict[str, Any]) -> str:
        prompt = (
            "You are an expert in software architecture and code analysis.\n"
            "Analyze the following codebase to identify UNIQUE microservice boundaries based on the actual code structure.\n"
            "Focus on business capabilities, data ownership, and actual code organization.\n\n"
        )
        
        # Include actual repository structure
        prompt += "## Repository Structure:\n"
        for file_path in sorted(parsed_files.keys())[:30]:  # Show first 30 files
            prompt += f"- {file_path}\n"
        
        prompt += "\n## Key Code Files Analysis:\n"
        # Include content from important files
        important_files = self._select_important_files(parsed_files)
        for file_path, file_info in important_files.items():
            content = file_info.get('content', '')[:1500]  # First 1500 chars
            prompt += f"\nFile: {file_path}\n``````\n"
        
        prompt += f"\n## Static Analysis Results:\n"
        for entity in static_analysis.get('entities', []):
            prompt += f"- Entity: {entity.get('name')} ({entity.get('type', 'class')})\n"
        
        for endpoint in static_analysis.get('api_endpoints', []):
            prompt += f"- API: {endpoint.get('method', 'GET')} {endpoint.get('route', '')}\n"
        
        prompt += (
            "\nBased on the actual code structure and content above, identify logical microservice boundaries.\n"
            "Return services that make sense for THIS specific codebase, not generic services.\n"
            "Consider domain-driven design principles and business capabilities.\n"
        )
        return prompt

    def _select_important_files(self, parsed_files: Dict[str, Any], max_files: int = 8) -> Dict[str, Any]:
        """Select the most important files for analysis"""
        important_files = {}
        
        # Prioritize controllers, services, models, entities
        priority_patterns = [
            'controller', 'service', 'model', 'entity', 'repository', 
            'api', 'manager', 'handler', 'processor', 'domain'
        ]
        
        for file_path, file_info in parsed_files.items():
            if len(important_files) >= max_files:
                break
                
            file_lower = file_path.lower()
            if any(pattern in file_lower for pattern in priority_patterns):
                important_files[file_path] = file_info
        
        # Fill remaining slots with largest files
        if len(important_files) < max_files:
            remaining_files = {k: v for k, v in parsed_files.items() if k not in important_files}
            sorted_files = sorted(remaining_files.items(), key=lambda x: x[1]['size'], reverse=True)
            for file_path, file_info in sorted_files[:max_files - len(important_files)]:
                important_files[file_path] = file_info
        
        return important_files
