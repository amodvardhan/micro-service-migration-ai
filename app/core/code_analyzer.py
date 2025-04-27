# Create app/core/code_analyzer.py
import os
import re
from typing import Dict, List, Any, Set, Tuple
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    """Advanced code analysis for identifying patterns and dependencies"""
    
    def __init__(self):
        self.language_analyzers = {
            "C#": self._analyze_csharp,
            "Python": self._analyze_python,
            "JavaScript": self._analyze_javascript,
            "TypeScript": self._analyze_typescript,
            "Java": self._analyze_java,
        }
    
    async def analyze_codebase(self, parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a complete codebase to extract patterns and dependencies"""
        results = {
            "entities": [],
            "dependencies": [],
            "api_endpoints": [],
            "namespaces": defaultdict(list),
            "potential_services": [],
            "language_distribution": defaultdict(int),
            "file_count": len(parsed_files)
        }
        
        # Process each file based on its language
        for file_path, file_info in parsed_files.items():
            try:
                extension = file_info.get("extension", "").lstrip(".")
                language = self._get_language_from_extension(extension)
                results["language_distribution"][language] += 1
                
                # Skip non-code files
                if language == "Unknown" or language in ["XML", "JSON", "YAML"]:
                    continue
                
                content = file_info.get("content", "")
                if not content:
                    continue
                
                # Apply language-specific analysis
                analyzer = self.language_analyzers.get(language)
                if analyzer:
                    file_analysis = await analyzer(file_path, content)
                    
                    # Merge results
                    results["entities"].extend(file_analysis.get("entities", []))
                    results["dependencies"].extend(file_analysis.get("dependencies", []))
                    results["api_endpoints"].extend(file_analysis.get("api_endpoints", []))
                    
                    # Add to namespace mapping
                    namespace = file_analysis.get("namespace")
                    if namespace:
                        results["namespaces"][namespace].append(file_path)
            
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {str(e)}")
        
        # Post-process results
        results["entities"] = self._deduplicate_entities(results["entities"])
        results["potential_services"] = self._identify_potential_services(
            results["entities"], 
            results["dependencies"],
            results["namespaces"]
        )
        
        return results
    
    async def _analyze_csharp(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze C# code to extract entities, dependencies, and patterns"""
        results = {
            "entities": [],
            "dependencies": [],
            "api_endpoints": [],
            "namespace": None
        }
        
        # Extract namespace
        namespace_match = re.search(r'namespace\s+([a-zA-Z0-9_.]+)', content)
        if namespace_match:
            results["namespace"] = namespace_match.group(1)
        
        # Extract classes and interfaces
        class_matches = re.finditer(r'(public|internal|private)?\s*(class|interface|record|struct)\s+([a-zA-Z0-9_]+)', content)
        for match in class_matches:
            entity_type = match.group(2)  # class, interface, etc.
            entity_name = match.group(3)  # name
            
            # Extract properties and methods
            properties = self._extract_csharp_properties(content, entity_name)
            methods = self._extract_csharp_methods(content, entity_name)
            
            results["entities"].append({
                "name": entity_name,
                "type": entity_type,
                "namespace": results["namespace"],
                "file_path": file_path,
                "properties": properties,
                "methods": methods
            })
        
        # Extract API endpoints (for controllers)
        if "Controller" in file_path or "controller" in content.lower():
            api_endpoints = self._extract_csharp_endpoints(content)
            results["api_endpoints"].extend(api_endpoints)
        
        # Extract dependencies
        dependencies = self._extract_csharp_dependencies(content)
        results["dependencies"].extend(dependencies)
        
        return results
    
    def _extract_csharp_properties(self, content: str, class_name: str) -> List[Dict[str, str]]:
        """Extract properties from C# class"""
        properties = []
        # Simple regex for property extraction - in a real implementation, use a proper parser
        prop_pattern = r'(public|private|protected|internal)?\s+([a-zA-Z0-9_<>]+)\s+([a-zA-Z0-9_]+)\s*{\s*get;'
        for match in re.finditer(prop_pattern, content):
            properties.append({
                "access": match.group(1) or "public",
                "type": match.group(2),
                "name": match.group(3)
            })
        return properties
    
    def _extract_csharp_methods(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """Extract methods from C# class"""
        methods = []
        # Simple regex for method extraction - in a real implementation, use a proper parser
        method_pattern = r'(public|private|protected|internal)?\s+([a-zA-Z0-9_<>]+)\s+([a-zA-Z0-9_]+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, content):
            methods.append({
                "access": match.group(1) or "public",
                "return_type": match.group(2),
                "name": match.group(3),
                "parameters": match.group(4)
            })
        return methods
    
    def _extract_csharp_endpoints(self, content: str) -> List[Dict[str, str]]:
        """Extract API endpoints from C# controller"""
        endpoints = []
        
        # Look for route attributes
        route_pattern = r'\[(?:Http(?:Get|Post|Put|Delete)|Route)\((?:\"|\')([^\"\']+)(?:\"|\')?\)\]'
        method_pattern = r'(public|private|protected)?\s+(?:async\s+)?([a-zA-Z0-9_<>]+)\s+([a-zA-Z0-9_]+)\s*\('
        
        # Find all route attributes
        for route_match in re.finditer(route_pattern, content):
            route = route_match.group(1)
            
            # Find the method that follows this route attribute
            content_after_route = content[route_match.end():]
            method_match = re.search(method_pattern, content_after_route)
            
            if method_match:
                method_name = method_match.group(3)
                return_type = method_match.group(2)
                
                # Determine HTTP method from attribute or default to GET
                http_method = "GET"
                if "HttpPost" in route_match.group(0):
                    http_method = "POST"
                elif "HttpPut" in route_match.group(0):
                    http_method = "PUT"
                elif "HttpDelete" in route_match.group(0):
                    http_method = "DELETE"
                
                endpoints.append({
                    "route": route,
                    "method": http_method,
                    "handler": method_name,
                    "return_type": return_type
                })
        
        return endpoints
    
    def _extract_csharp_dependencies(self, content: str) -> List[Dict[str, str]]:
        """Extract dependencies from C# code"""
        dependencies = []
        
        # Extract using statements
        using_pattern = r'using\s+([a-zA-Z0-9_.]+);'
        for match in re.finditer(using_pattern, content):
            namespace = match.group(1)
            dependencies.append({
                "type": "namespace",
                "name": namespace
            })
        
        # Extract direct class references
        # This is a simplified approach - a real implementation would use a proper parser
        class_ref_pattern = r'new\s+([a-zA-Z0-9_]+)[\s\(]'
        for match in re.finditer(class_ref_pattern, content):
            class_name = match.group(1)
            if class_name not in ["string", "int", "bool", "var", "object"]:
                dependencies.append({
                    "type": "class",
                    "name": class_name
                })
        
        return dependencies
    
    async def _analyze_python(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Python code to extract entities, dependencies, and patterns"""
        # Similar implementation for Python
        # For brevity, this is a placeholder - implement similar to C# analyzer
        results = {
            "entities": [],
            "dependencies": [],
            "api_endpoints": [],
            "namespace": os.path.dirname(file_path).replace("/", ".")
        }
        
        # Extract classes
        class_pattern = r'class\s+([a-zA-Z0-9_]+)(?:\(([a-zA-Z0-9_, ]+)\))?:'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            parent_classes = match.group(2).split(',') if match.group(2) else []
            
            results["entities"].append({
                "name": class_name,
                "type": "class",
                "namespace": results["namespace"],
                "file_path": file_path,
                "parent_classes": [p.strip() for p in parent_classes if p.strip()]
            })
        
        # Extract API endpoints (for Flask/FastAPI)
        if "app.route" in content or "@app" in content:
            api_endpoints = self._extract_python_endpoints(content)
            results["api_endpoints"].extend(api_endpoints)
        
        # Extract imports
        import_pattern = r'(?:from\s+([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_, ]+))|(?:import\s+([a-zA-Z0-9_.]+))'
        for match in re.finditer(import_pattern, content):
            if match.group(1) and match.group(2):  # from X import Y
                module = match.group(1)
                imports = [imp.strip() for imp in match.group(2).split(',')]
                for imp in imports:
                    results["dependencies"].append({
                        "type": "module",
                        "name": f"{module}.{imp}"
                    })
            elif match.group(3):  # import X
                module = match.group(3)
                results["dependencies"].append({
                    "type": "module",
                    "name": module
                })
        
        return results
    
    def _extract_python_endpoints(self, content: str) -> List[Dict[str, str]]:
        """Extract API endpoints from Python web frameworks"""
        endpoints = []
        
        # Flask routes
        flask_pattern = r'@app.route\([\'"]([^\'"]+)[\'"](?:,\s*methods=\[([^\]]+)\])?\)'
        for match in re.finditer(flask_pattern, content):
            route = match.group(1)
            methods = match.group(2) if match.group(2) else "'GET'"
            methods = [m.strip().strip("'\"") for m in methods.split(',')]
            
            # Find the function that follows this route
            content_after_route = content[match.end():]
            func_match = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', content_after_route)
            
            if func_match:
                func_name = func_match.group(1)
                for method in methods:
                    endpoints.append({
                        "route": route,
                        "method": method,
                        "handler": func_name
                    })
        
        # FastAPI routes
        fastapi_patterns = [
            r'@app.get\([\'"]([^\'"]+)[\'"]',
            r'@app.post\([\'"]([^\'"]+)[\'"]',
            r'@app.put\([\'"]([^\'"]+)[\'"]',
            r'@app.delete\([\'"]([^\'"]+)[\'"]'
        ]
        
        for i, pattern in enumerate(fastapi_patterns):
            method = ["GET", "POST", "PUT", "DELETE"][i]
            for match in re.finditer(pattern, content):
                route = match.group(1)
                
                # Find the function that follows this route
                content_after_route = content[match.end():]
                func_match = re.search(r'(?:async\s+)?def\s+([a-zA-Z0-9_]+)\s*\(', content_after_route)
                
                if func_match:
                    func_name = func_match.group(1)
                    endpoints.append({
                        "route": route,
                        "method": method,
                        "handler": func_name
                    })
        
        return endpoints
    
    async def _analyze_javascript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze JavaScript code to extract entities, dependencies, and patterns"""
        # Placeholder - implement similar to other analyzers
        return {
            "entities": [],
            "dependencies": [],
            "api_endpoints": [],
            "namespace": None
        }
    
    async def _analyze_typescript(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze TypeScript code to extract entities, dependencies, and patterns"""
        # Placeholder - implement similar to other analyzers
        return {
            "entities": [],
            "dependencies": [],
            "api_endpoints": [],
            "namespace": None
        }
    
    async def _analyze_java(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Java code to extract entities, dependencies, and patterns"""
        # Placeholder - implement similar to other analyzers
        return {
            "entities": [],
            "dependencies": [],
            "api_endpoints": [],
            "namespace": None
        }
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities based on name and namespace"""
        unique_entities = {}
        for entity in entities:
            key = f"{entity.get('namespace', '')}.{entity.get('name', '')}"
            if key not in unique_entities:
                unique_entities[key] = entity
        
        return list(unique_entities.values())
    
    def _identify_potential_services(self, entities: List[Dict[str, Any]], 
                                   dependencies: List[Dict[str, Any]],
                                   namespaces: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        """Identify potential microservice boundaries based on code analysis"""
        # This is a simplified approach - a real implementation would use more sophisticated
        # algorithms like community detection on the dependency graph
        
        # Group entities by namespace
        namespace_entities = defaultdict(list)
        for entity in entities:
            namespace = entity.get("namespace")
            if namespace:
                namespace_entities[namespace].append(entity)
        
        # Identify potential services based on namespace grouping
        potential_services = []
        for namespace, ns_entities in namespace_entities.items():
            # Skip namespaces with too few entities
            if len(ns_entities) < 2:
                continue
            
            # Extract domain concepts from namespace
            domain_concept = self._extract_domain_concept(namespace)
            if not domain_concept:
                continue
            
            # Create a potential service
            service = {
                "name": f"{domain_concept.title()}Service",
                "namespace": namespace,
                "entities": [e["name"] for e in ns_entities],
                "files": namespaces.get(namespace, []),
                "api_endpoints": []
            }
            
            potential_services.append(service)
        
        return potential_services
    
    def _extract_domain_concept(self, namespace: str) -> str:
        """Extract domain concept from namespace"""
        # Extract the last part of the namespace
        parts = namespace.split('.')
        if not parts:
            return ""
        
        # Use the last meaningful part
        for part in reversed(parts):
            if part.lower() not in ["models", "controllers", "services", "repositories", "data", "core", "api", "web"]:
                return part
        
        return parts[-1]
    
    def _get_language_from_extension(self, extension: str) -> str:
        """Map file extension to programming language"""
        language_map = {
            "py": "Python",
            "js": "JavaScript",
            "ts": "TypeScript",
            "java": "Java",
            "cs": "C#",
            "cpp": "C++",
            "c": "C",
            "go": "Go",
            "rb": "Ruby",
            "php": "PHP",
            "html": "HTML",
            "css": "CSS",
            "json": "JSON",
            "xml": "XML",
            "yaml": "YAML",
            "yml": "YAML",
            "md": "Markdown",
            "sql": "SQL",
            "sh": "Shell",
            "bat": "Batch",
            "ps1": "PowerShell",
            "csproj": "XML",
            "sln": "Solution"
        }
        
        return language_map.get(extension.lower(), "Unknown")
