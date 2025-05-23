import os
import re
import json
from typing import Dict, Any, List
from app.core.llm_service import LLMService
from pydantic import BaseModel, ValidationError
import logging
from .templates.template_factory import TemplateFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_CHUNK_SIZE = 2000
MAX_FILES_PER_BATCH = 6

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
        self.template_factory = TemplateFactory()

    async def refactor_code(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"Refactoring code for service: {service_boundary.get('name')}, files: {len(original_code)}")
        
        if not original_code:
            logger.warning("No files passed to DeveloperAgent")
            return {
                "service_name": service_boundary.get("name"),
                "files": self.template_factory.create_service_files(service_boundary, {})
            }

        # Detect language first
        language = self.template_factory.detect_language(original_code)
        logger.info(f"Detected language: {language}")

        all_files = list(original_code.items())
        microservice_files = []

        # Process files in batches to avoid LLM context overflow
        for i in range(0, len(all_files), MAX_FILES_PER_BATCH):
            batch = dict(all_files[i:i+MAX_FILES_PER_BATCH])
            logger.info(f"Processing batch {i//MAX_FILES_PER_BATCH + 1} with {len(batch)} files")
            
            prompt = self._prepare_refactoring_prompt(service_boundary, batch, language)
            prompt += (
                "\n\nIMPORTANT: Return ONLY a valid JSON object. Do not include any explanations or markdown.\n"
                "Schema:\n"
                "{\n"
                "  \"service_name\": \"string\",\n"
                "  \"files\": [\n"
                "    {\"path\": \"string\", \"content\": \"string\"}\n"
                "  ]\n"
                "}\n"
                "Escape all quotes and special characters in the content field properly."
            )

            try:
                llm_response = await self.llm_service.generate_completion(prompt)
                content = llm_response.get("content", "")
                logger.info(f"DeveloperAgent LLM output: {content[:300]}...")
                
                # Try multiple JSON extraction methods
                parsed_files = self._robust_json_extraction(content)
                if parsed_files:
                    microservice_files.extend(parsed_files)
                    logger.info(f"Successfully parsed {len(parsed_files)} files from batch")
                else:
                    logger.warning(f"No valid files extracted from batch {i//MAX_FILES_PER_BATCH + 1}")
                    
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")

        if microservice_files:
            # Deduplicate files by path
            unique_files = {}
            for f in microservice_files:
                unique_files[f["path"]] = f
            
            logger.info(f"Generated {len(unique_files)} unique files for {service_boundary.get('name')}")
            return {
                "service_name": service_boundary.get("name"),
                "files": list(unique_files.values())
            }
        else:
            logger.warning(f"No files generated for {service_boundary.get('name')}, creating fallback service")
            return {
                "service_name": service_boundary.get("name"),
                "files": self.template_factory.create_service_files(service_boundary, original_code)
            }

    def _robust_json_extraction(self, content: str) -> List[Dict[str, str]]:
        """Try multiple methods to extract valid JSON from LLM response"""
        
        # Method 1: Standard JSON extraction
        try:
            json_str = self._extract_json_from_response(content)
            if json_str:
                llm_json = json.loads(json_str)
                if "files" in llm_json and isinstance(llm_json["files"], list):
                    valid_files = [f for f in llm_json["files"] if isinstance(f, dict) and "path" in f and "content" in f]
                    if valid_files:
                        return valid_files
        except Exception as e:
            logger.debug(f"Method 1 failed: {str(e)}")

        # Method 2: Clean and retry JSON parsing
        try:
            json_str = self._extract_json_from_response(content)
            if json_str:
                # Clean the JSON string
                cleaned_json = self._clean_json_string(json_str)
                llm_json = json.loads(cleaned_json)
                if "files" in llm_json and isinstance(llm_json["files"], list):
                    valid_files = [f for f in llm_json["files"] if isinstance(f, dict) and "path" in f and "content" in f]
                    if valid_files:
                        return valid_files
        except Exception as e:
            logger.debug(f"Method 2 failed: {str(e)}")

        # Method 3: Regex extraction as fallback
        try:
            return self._extract_files_with_regex(content)
        except Exception as e:
            logger.debug(f"Method 3 failed: {str(e)}")

        # Method 4: Line-by-line parsing for severely malformed JSON
        try:
            return self._extract_files_line_by_line(content)
        except Exception as e:
            logger.debug(f"Method 4 failed: {str(e)}")

        return []

    def _clean_json_string(self, json_str: str) -> str:
        """Clean JSON string to fix common issues"""
        # Remove any text before the first {
        start_idx = json_str.find("{")
        if start_idx > 0:
            json_str = json_str[start_idx:]
        
        # Remove any text after the last }
        end_idx = json_str.rfind("}")
        if end_idx >= 0:
            json_str = json_str[:end_idx + 1]
        
        # Fix common JSON issues
        # 1. Replace unescaped newlines in strings
        json_str = re.sub(r'(?<!\\)\n(?=.*")', '\\n', json_str)
        
        # 2. Replace unescaped tabs
        json_str = re.sub(r'(?<!\\)\t', '\\t', json_str)
        
        # 3. Fix unescaped quotes (but be careful not to break valid JSON)
        # This is a simplified approach - in production you might want more sophisticated handling
        json_str = re.sub(r'(?<!\\)"(?![,}\]:\s])', '\\"', json_str)
        
        # 4. Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        return json_str

    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from LLM response, handling various formats"""
        if "```json" in content:
            start_idx = content.find("``````json")
            # Find the next closing ```
            end_idx = content.find("```", start_idx)
            if end_idx == -1:
                json_str = content[start_idx:]
            else:
                json_str = content[start_idx:end_idx]
            return json_str.strip()
        
        # Case 2: Response contains a JSON object without markdown
        json_start = content.find("{")
        json_end = content.rfind("}")
        
        if json_start >= 0 and json_end >= 0:
            json_str = content[json_start:json_end+1]
            return json_str.strip()
        
        logger.error("No JSON object found in response")
        return ""

    def _extract_files_with_regex(self, content: str) -> List[Dict[str, str]]:
        """Extract files using regex as fallback"""
        try:
            files = []
            
            # Pattern to match file objects in JSON
            file_pattern = r'"path"\s*:\s*"([^"]+)"\s*,\s*"content"\s*:\s*"((?:[^"\$$|\\.)*)"'
            matches = re.findall(file_pattern, content, re.DOTALL)
            
            for path, content_match in matches:
                # Unescape content
                try:
                    unescaped_content = content_match.encode().decode('unicode_escape')
                except:
                    unescaped_content = content_match
                
                files.append({"path": path, "content": unescaped_content})
            
            if files:
                logger.info(f"Extracted {len(files)} files using regex fallback")
            
            return files
        except Exception as e:
            logger.error(f"Regex extraction failed: {str(e)}")
            return []

    def _extract_files_line_by_line(self, content: str) -> List[Dict[str, str]]:
        """Extract files by parsing line by line - last resort method"""
        try:
            files = []
            lines = content.split('\n')
            current_file = {}
            in_content = False
            content_lines = []
            
            for line in lines:
                line = line.strip()
                
                if '"path"' in line and ':' in line:
                    # Extract path
                    path_match = re.search(r'"path"\s*:\s*"([^"]+)"', line)
                    if path_match:
                        if current_file and 'path' in current_file:
                            # Save previous file
                            current_file['content'] = '\n'.join(content_lines)
                            files.append(current_file)
                        
                        current_file = {'path': path_match.group(1)}
                        content_lines = []
                        in_content = False
                
                elif '"content"' in line and ':' in line:
                    in_content = True
                    # Try to extract content from same line
                    content_match = re.search(r'"content"\s*:\s*"(.*)"', line)
                    if content_match:
                        content_lines.append(content_match.group(1))
                
                elif in_content and current_file:
                    # Accumulate content lines
                    content_lines.append(line.replace('"', '').replace(',', ''))
            
            # Save last file
            if current_file and 'path' in current_file:
                current_file['content'] = '\n'.join(content_lines)
                files.append(current_file)
            
            if files:
                logger.info(f"Extracted {len(files)} files using line-by-line parsing")
            
            return files
        except Exception as e:
            logger.error(f"Line-by-line extraction failed: {str(e)}")
            return []

    def _prepare_refactoring_prompt(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any], language: str) -> str:
        prompt = f"Refactor the following {language} code to create a microservice for '{service_boundary['name']}'.\n\n"
        prompt += f"Service Name: {service_boundary['name']}\n"
        prompt += f"Primary Language: {language}\n"
        prompt += f"Description: {service_boundary.get('description', 'N/A')}\n"
        prompt += f"Responsibilities: {', '.join(service_boundary.get('responsibilities', []))}\n"
        prompt += f"Entities: {', '.join(service_boundary.get('entities', []))}\n"
        prompt += f"APIs: {', '.join(service_boundary.get('apis', []))}\n\n"
        prompt += "Original Code:\n"
        
        for file_path, file_info in original_code.items():
            content = file_info.get('content', '')
            if len(content) <= MAX_CHUNK_SIZE:
                prompt += f"File: {file_path}\n```\n{content}\n```"
            else:
                for i in range(0, len(content), MAX_CHUNK_SIZE):
                    chunk = content[i:i+MAX_CHUNK_SIZE]
                    prompt += f"File: {file_path} (chunk {i//MAX_CHUNK_SIZE + 1})\n```\n{chunk}\n```"
        
        prompt += f"""Please refactor this {language} code to create a microservice with the following:
                1. Controllers/Handlers for the API endpoints (appropriate for {language})
                2. Models/Entities for the core data structures
                3. Services for the business logic
                4. Data access layer (appropriate for {language})
                5. Configuration files appropriate for {language}
                6. README file explaining the microservice

                Generate code that follows {language} best practices and conventions.
                For each file, provide a valid path and full code content.

                IMPORTANT: Ensure all quotes and special characters in code content are properly escaped for JSON."""
        
        return prompt
