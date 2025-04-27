from typing import Dict, Any, List
from app.core.llm_service import LLMService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArchitectAgent:
    """Agent for architectural analysis and service boundary identification"""
    
    def __init__(self, llm_service: LLMService):
        """Initialize the agent with the LLM service"""
        self.llm_service = llm_service
        
    async def identify_service_boundaries(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Identify logical service boundaries based on code analysis"""
        # Prepare prompt for the LLM
        prompt = self._prepare_boundary_detection_prompt(analysis_results)
        
        # Get service boundary suggestions from LLM
        boundaries_response = await self.llm_service.generate_completion(prompt)
        
        # Parse the LLM response
        try:
            # Extract structured information from the LLM response
            content = boundaries_response.get("content", "")
            
            # For now, return a placeholder
            # In a real implementation, you would parse the LLM response
            boundaries = {
                'service_boundaries': [
                    {
                        'name': 'UserService',
                        'description': 'Handles user authentication and profile management',
                        'responsibilities': ['User registration', 'Authentication', 'Profile management'],
                        'entities': ['User', 'UserProfile', 'Role'],
                        'apis': ['/api/users', '/api/auth'],
                        'files': analysis_results.get('namespaces', {}).get('UserManagement', [])
                    },
                    {
                        'name': 'ProductService',
                        'description': 'Manages product catalog and inventory',
                        'responsibilities': ['Product management', 'Inventory tracking', 'Category management'],
                        'entities': ['Product', 'Category', 'Inventory'],
                        'apis': ['/api/products', '/api/categories'],
                        'files': analysis_results.get('namespaces', {}).get('ProductManagement', [])
                    },
                    {
                        'name': 'OrderService',
                        'description': 'Handles order processing and management',
                        'responsibilities': ['Order creation', 'Order processing', 'Order history'],
                        'entities': ['Order', 'OrderItem', 'Payment'],
                        'apis': ['/api/orders', '/api/payments'],
                        'files': analysis_results.get('namespaces', {}).get('OrderManagement', [])
                    }
                ],
                'rationale': 'The service boundaries were identified based on domain-driven design principles, focusing on business capabilities and data cohesion.',
                'communication_patterns': [
                    {
                        'source': 'OrderService',
                        'target': 'ProductService',
                        'type': 'Synchronous',
                        'purpose': 'Check product availability'
                    },
                    {
                        'source': 'OrderService',
                        'target': 'UserService',
                        'type': 'Synchronous',
                        'purpose': 'Validate user'
                    }
                ]
            }
            
            return boundaries
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            return {}
        
    def _prepare_boundary_detection_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """Prepare a prompt for service boundary detection"""
        prompt = "Based on the following code analysis, identify logical microservice boundaries:\n\n"
        
        # Add analysis results to the prompt
        prompt += f"Architecture Type: {analysis_results.get('architecture_type', 'Unknown')}\n"
        
        # Add potential services from analysis
        prompt += "\nPotential Services from Analysis:\n"
        for service in analysis_results.get('potential_services', []):
            prompt += f"- {service.get('name')}\n"
            prompt += f"  - Entities: {', '.join(service.get('entities', []))}\n"
        
        # Add entities
        prompt += "\nEntities:\n"
        for entity in analysis_results.get('entities', [])[:10]:  # Limit to 10 for brevity
            prompt += f"- {entity.get('name')} ({entity.get('type', 'class')})\n"
        
        # Add API endpoints
        prompt += "\nAPI Endpoints:\n"
        for endpoint in analysis_results.get('api_endpoints', [])[:10]:  # Limit to 10 for brevity
            prompt += f"- {endpoint.get('method', 'GET')} {endpoint.get('route')}\n"
        
        prompt += "\nPlease identify logical microservice boundaries based on the following principles:\n"
        prompt += "1. Domain-Driven Design (DDD) concepts\n"
        prompt += "2. High cohesion and low coupling\n"
        prompt += "3. Single Responsibility Principle\n"
        prompt += "4. Business capabilities\n\n"
        
        prompt += "For each identified microservice, provide:\n"
        prompt += "1. Service name\n"
        prompt += "2. Description\n"
        prompt += "3. Key responsibilities\n"
        prompt += "4. Core entities/models\n"
        prompt += "5. API endpoints\n"
        prompt += "6. Communication patterns with other services\n"
        
        return prompt
