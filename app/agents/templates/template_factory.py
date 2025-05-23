from typing import Dict, Any, List, Optional
from .base_template import BaseTemplate
from .csharp_template import CSharpTemplate
from .java_template import JavaTemplate
from .python_template import PythonTemplate
from .javascript_template import JavaScriptTemplate
from .go_template import GoTemplate

class GenericTemplate(BaseTemplate):
    def get_language_name(self) -> str:
        return "Generic"
    
    def get_file_extensions(self) -> List[str]:
        return []
    
    def get_dockerfile_template(self) -> str:
        return """FROM alpine:latest
WORKDIR /app
COPY . .
EXPOSE 8080
CMD ["echo", "Generic service template"]"""
    
    def get_prerequisites(self) -> str:
        return "Appropriate runtime for the language"
    
    def get_local_run_instructions(self, service_name: str) -> str:
        return f"""```
# Follow language-specific instructions to run {service_name}
```"""
    
    def generate_main_files(self, service_name: str) -> List[Dict[str, str]]:
        return [
            {
                "path": f"{service_name}/main.txt",
                "content": f"Main application file for {service_name}\n\nThis is a placeholder file for the main application logic."
            },
            {
                "path": f"{service_name}/config.txt",
                "content": f"Configuration file for {service_name}\n\nAdd your configuration settings here."
            }
        ]

class TemplateFactory:
    """Factory class to create language-specific templates"""
    
    def __init__(self):
        self._templates = {
            "C#": CSharpTemplate(),
            "Java": JavaTemplate(),
            "Python": PythonTemplate(),
            "JavaScript": JavaScriptTemplate(),
            "Go": GoTemplate(),
            "Generic": GenericTemplate()
        }
    
    def get_template(self, language: str) -> BaseTemplate:
        """Get template for specified language"""
        return self._templates.get(language, self._templates["Generic"])
    
    def detect_language(self, original_code: Dict[str, Any]) -> str:
        """Detect the primary language for this specific service"""
        language_counts = {}
        
        for file_path, file_info in original_code.items():
            ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
            
            if ext in ['cs', 'csproj']:
                language_counts['C#'] = language_counts.get('C#', 0) + 1
            elif ext in ['java', 'gradle']:
                language_counts['Java'] = language_counts.get('Java', 0) + 1
            elif ext == 'py':
                language_counts['Python'] = language_counts.get('Python', 0) + 1
            elif ext in ['js', 'ts']:
                language_counts['JavaScript'] = language_counts.get('JavaScript', 0) + 1
            elif ext == 'go':
                language_counts['Go'] = language_counts.get('Go', 0) + 1
        
        return max(language_counts, key=language_counts.get) if language_counts else "Generic"
    
    def create_service_files(self, service_boundary: Dict[str, Any], original_code: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create complete service file structure"""
        language = self.detect_language(original_code)
        template = self.get_template(language)
        return template.create_service_files(service_boundary)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self._templates.keys())
