import os
import tempfile
import git
from typing import Dict, Any, List
import glob
from app.core.llm_service import LLMService

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
    """Agent for analyzing code repositories"""
    
    def __init__(self, llm_service: LLMService):
        """Initialize the agent with the LLM service"""
        self.llm_service = llm_service
        self.code_parser = CodeParser()
        
    async def analyze_repository(self, repo_url: str) -> Dict[str, Any]:
        """Analyze a code repository to understand its structure"""
        # Clone repository
        repo_path = await self.code_parser.clone_repository(repo_url)
        
        # Parse code files
        parsed_files = await self.code_parser.parse_directory(repo_path)
        
        # Generate code embeddings for semantic understanding
        # This is a simplified version - in a real implementation,
        # you would process files in batches to avoid token limits
        sample_files = self._select_representative_files(parsed_files)
        file_contents = [file_info['content'] for file_info in sample_files.values()]
        
        # Generate embeddings
        # Note: This is commented out to avoid making API calls during setup
        # embeddings = await self.llm_service.generate_embeddings(file_contents)
        
        # Use LLM to analyze dependencies and patterns
        analysis_results = await self._analyze_with_llm(parsed_files)
        
        return {
            'repo_path': repo_path,
            'parsed_files': parsed_files,
            'analysis_results': analysis_results
        }
        
    def _select_representative_files(self, parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        """Select a representative subset of files for analysis"""
        # This is a simplified version - in a real implementation,
        # you would use more sophisticated selection criteria
        sample_size = min(10, len(parsed_files))
        sample_files = {}
        
        for i, (file_path, file_info) in enumerate(parsed_files.items()):
            if i >= sample_size:
                break
            sample_files[file_path] = file_info
            
        return sample_files
        
    async def _analyze_with_llm(self, parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code files with the LLM"""
        # Select a subset of files for the initial analysis
        sample_files = self._select_representative_files(parsed_files)
        
        # Prepare the prompt
        prompt = self._prepare_analysis_prompt(sample_files)
        
        # Get analysis from LLM
        # Note: This is a simplified version to avoid making API calls during setup
        # analysis = await self.llm_service.generate_completion(prompt)
        
        # For now, return a placeholder
        return {
            'architecture_type': 'monolith',
            'languages': ['C#'],
            'frameworks': ['.NET'],
            'potential_services': [
                {'name': 'UserService', 'files': []},
                {'name': 'ProductService', 'files': []},
                {'name': 'OrderService', 'files': []}
            ]
        }
        
    def _prepare_analysis_prompt(self, sample_files: Dict[str, Any]) -> str:
        """Prepare a prompt for code analysis"""
        prompt = "Analyze the following code files to understand the architecture and identify potential microservice boundaries:\n\n"
        
        for file_path, file_info in sample_files.items():
            prompt += f"File: {file_path}\n"
            prompt += f"```\n"
            
            # Limit content length to avoid token limits
            content = file_info['content']
            if len(content) > 1000:
                content = content[:1000] + "...[truncated]"
                
            prompt += content + "\n```\n\n"
            
        prompt += "Please provide the following information:\n"
        prompt += "1. What type of architecture is this (monolith, microservices, etc.)?\n"
        prompt += "2. What languages and frameworks are used?\n"
        prompt += "3. Identify potential microservice boundaries based on the code.\n"
        
        return prompt