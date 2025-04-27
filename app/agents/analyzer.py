import os
import tempfile
import git
from typing import Dict, Any, List
import glob
from app.core.llm_service import LLMService
from app.knowledge.embedding_manager import EmbeddingManager
from app.core.code_analyzer import CodeAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeParser:
    """Parses code files from a repository"""
    
    async def clone_repository(self, repo_url: str) -> str:
        """Clone a repository and return the path to the cloned directory"""
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Clone the repository
            git.Repo.clone_from(repo_url, temp_dir)
            
            return temp_dir
        except Exception as e:
            print(f"Error cloning repository: {str(e)}")
            raise
            
    async def parse_directory(self, directory_path: str) -> Dict[str, Any]:
        """Parse all code files in the given directory"""
        parsed_files = {}
        
        # Get all code files
        code_files = self._find_code_files(directory_path)
        
        for file_path in code_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Get relative path for better organization
                relative_path = os.path.relpath(file_path, directory_path)
                parsed_files[relative_path] = {
                    'content': content,
                    'extension': os.path.splitext(file_path)[1],
                    'size': os.path.getsize(file_path)
                }
            except Exception as e:
                print(f"Error parsing file {file_path}: {str(e)}")
                
        return parsed_files
        
    def _find_code_files(self, directory_path: str) -> List[str]:
        """Find all code files in the given directory"""
        # Define extensions to look for
        extensions = [
            '.cs', '.csproj', '.sln',  # .NET files
            '.py', '.js', '.ts', '.java', '.go',  # Other common languages
            '.xml', '.json', '.yaml', '.yml'  # Config files
        ]
        
        code_files = []
        
        for ext in extensions:
            pattern = os.path.join(directory_path, '**', f'*{ext}')
            code_files.extend(glob.glob(pattern, recursive=True))
            
        return code_files

class CodeAnalysisAgent:
    """Agent for analyzing code repositories with enhanced embedding capabilities"""
    
    def __init__(self, llm_service: LLMService, embedding_manager: EmbeddingManager):
        """Initialize the agent with the LLM service and embedding manager"""
        self.llm_service = llm_service
        self.embedding_manager = embedding_manager
        self.code_parser = CodeParser()
        self.code_analyzer = CodeAnalyzer() 
        
    async def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a code repository to understand its structure"""
        try:
            # Clone repository
            logger.info(f"Cloning repository: {repo_url}")
            repo_path = await self.code_parser.clone_repository(repo_url)
            
            # Parse code files
            logger.info(f"Parsing code files from repository")
            parsed_files = await self.code_parser.parse_directory(repo_path)
            logger.info(f"Found {len(parsed_files)} files in repository")
            
            # Process embeddings for all files
            logger.info("Generating and storing embeddings for code files")
            embedding_results = await self.embedding_manager.process_codebase(parsed_files)
            logger.info(f"Processed {embedding_results['processed_files']} files for embeddings")
            
            # Perform static code analysis
            logger.info("Performing static code analysis")
            static_analysis = await self.code_analyzer.analyze_codebase(parsed_files)
            logger.info(f"Identified {len(static_analysis['entities'])} entities and {len(static_analysis['potential_services'])} potential services")
            
            # Select representative files for LLM analysis
            sample_files = self._select_representative_files(parsed_files)
            
            # Use LLM to analyze dependencies and patterns
            logger.info("Analyzing code structure and dependencies with LLM")
            llm_analysis = await self._analyze_with_llm(sample_files, static_analysis)
            
            # Combine static analysis with LLM insights
            analysis_results = self._combine_analysis_results(static_analysis, llm_analysis)
            
            # Enhance analysis with semantic similarity insights
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
    
    async def _generate_semantic_insights(self, parsed_files: Dict[str, Any], 
                                       embedding_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate semantic insights based on code embeddings"""
        # This is a placeholder - in a real implementation, you would:
        # 1. Identify clusters of semantically similar files
        # 2. Find potential service boundaries based on semantic similarity
        # 3. Identify code duplication or reuse opportunities
        
        return {
            "similar_file_groups": [],
            "potential_boundaries": [],
            "duplication_candidates": []
        }
    
    def _combine_analysis_results(self, static_analysis: Dict[str, Any], llm_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine static analysis with LLM insights"""
        combined = {**static_analysis}
        
        # Merge potential services, giving priority to LLM suggestions
        llm_services = llm_analysis.get("potential_services", [])
        if llm_services:
            # Create a mapping of service names from static analysis
            static_service_map = {s["name"]: s for s in static_analysis.get("potential_services", [])}
            
            # Merge or add LLM services
            merged_services = []
            for llm_service in llm_services:
                service_name = llm_service["name"]
                if service_name in static_service_map:
                    # Merge with static analysis service
                    merged_service = {**static_service_map[service_name], **llm_service}
                    # Ensure we keep all entities
                    merged_service["entities"] = list(set(
                        static_service_map[service_name].get("entities", []) + 
                        llm_service.get("entities", [])
                    ))
                    merged_services.append(merged_service)
                else:
                    merged_services.append(llm_service)
            
            # Add any static services not covered by LLM
            for static_service in static_analysis.get("potential_services", []):
                if static_service["name"] not in [s["name"] for s in merged_services]:
                    merged_services.append(static_service)
            
            combined["potential_services"] = merged_services
        
        # Add LLM-specific insights
        combined["architecture_type"] = llm_analysis.get("architecture_type", "Unknown")
        combined["architecture_insights"] = llm_analysis.get("architecture_insights", {})
        
        return combined
    
    async def _analyze_with_llm(self, sample_files: Dict[str, Any], static_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code files with the LLM, incorporating static analysis results"""
        # Prepare the prompt
        prompt = self._prepare_analysis_prompt(sample_files, static_analysis)
        
        # Get analysis from LLM
        analysis_response = await self.llm_service.generate_completion(prompt)
        
        # Parse the LLM response
        try:
            # Extract structured information from the LLM response
            content = analysis_response.get("content", "")
            
            # For now, return a placeholder
            # In a real implementation, you would parse the LLM response
            return {
                'architecture_type': 'monolith',
                'architecture_insights': {
                    'coupling': 'high',
                    'cohesion': 'low',
                    'scalability_issues': ['shared database', 'tight coupling']
                },
                'potential_services': [
                    {'name': 'UserService', 'entities': ['User', 'UserProfile', 'Role'], 'responsibilities': ['Authentication', 'User Management']},
                    {'name': 'ProductService', 'entities': ['Product', 'Category', 'Inventory'], 'responsibilities': ['Product Catalog', 'Inventory Management']},
                    {'name': 'OrderService', 'entities': ['Order', 'OrderItem', 'Payment'], 'responsibilities': ['Order Processing', 'Payment Handling']}
                ]
            }
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {}
    
    def _prepare_analysis_prompt(self, sample_files: Dict[str, Any], static_analysis: Dict[str, Any]) -> str:
        """Prepare a prompt for code analysis, incorporating static analysis results"""
        prompt = "Analyze the following code files and static analysis results to understand the architecture and identify potential microservice boundaries:\n\n"
        
        # Add static analysis summary
        prompt += "## Static Analysis Summary\n"
        prompt += f"- Found {len(static_analysis.get('entities', []))} entities\n"
        prompt += f"- Found {len(static_analysis.get('api_endpoints', []))} API endpoints\n"
        prompt += f"- Found {len(static_analysis.get('namespaces', {}))} namespaces\n"
        prompt += f"- Identified {len(static_analysis.get('potential_services', []))} potential services\n\n"
        
        # Add potential services from static analysis
        prompt += "## Potential Services Identified by Static Analysis\n"
        for service in static_analysis.get('potential_services', [])[:5]:  # Limit to 5 for brevity
            prompt += f"- {service.get('name')}\n"
            prompt += f"  - Namespace: {service.get('namespace')}\n"
            prompt += f"  - Entities: {', '.join(service.get('entities', []))}\n"
        prompt += "\n"
        
        # Add sample files
        prompt += "## Sample Code Files\n"
        for file_path, file_info in list(sample_files.items())[:3]:  # Limit to 3 files for token management
            prompt += f"File: {file_path}\n"
            prompt += f"```\n"
            
            # Limit content length to avoid token limits
            content = file_info.get('content', '')
            if len(content) > 1000:
                content = content[:1000] + "...[truncated]"
                
            prompt += content + "\n```\n\n"
        
        prompt += "Please provide the following information:\n"
        prompt += "1. What type of architecture is this (monolith, microservices, etc.)?\n"
        prompt += "2. What are the key architectural insights (coupling, cohesion, scalability issues)?\n"
        prompt += "3. Identify potential microservice boundaries based on the code and static analysis.\n"
        prompt += "4. For each potential microservice, list:\n"
        prompt += "   a. Service name\n"
        prompt += "   b. Core entities/models\n"
        prompt += "   c. Key responsibilities\n"
        
        return prompt