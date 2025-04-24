from typing import Dict, Any, List
from app.core.llm_service import LLMService

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
        # Note: This is commented out to avoid making API calls during setup
        # boundaries = await self.llm_service.generate_completion(prompt)
        
        # For now, return a placeholder
        boundaries = {
            'service_boundaries': [
                {
                    'name': 'UserService',
                    'description': 'Handles user authentication and profile management',
                    'responsibilities': ['User registration', 'Authentication', 'Profile management'],
                    'entities': ['User', 'UserProfile', 'Role'],
                    'apis': ['/api/users', '/api/auth']
                },
                {
                    'name': 'ProductService',
                    'description': 'Manages product catalog and inventory',
                    'responsibilities': ['Product management', 'Inventory tracking', 'Category management'],
                    'entities': ['Product', 'Category', 'Inventory'],
                    'apis': ['/api/products', '/api/categories']
                },
                {
                    'name': 'OrderService',
                    'description': 'Handles order processing and management',
                    'responsibilities': ['Order creation', 'Order processing', 'Order history'],
                    'entities': ['Order', 'OrderItem', 'Payment'],
                    'apis': ['/api/orders', '/api/payments']
                }
            ],
            'rationale': 'The service boundaries were identified based on domain-driven design principles, focusing on business capabilities and data cohesion.'
        }
        
        return boundaries
        
    def _prepare_boundary_detection_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """Prepare a prompt for service boundary detection"""
        prompt = "Based on the following code analysis, identify logical microservice boundaries:\n\n"
        
        # Add analysis results to the prompt
        prompt += f"Architecture Type: {analysis_results.get('architecture_type', 'Unknown')}\n"
        prompt += f"Languages: {', '.join(analysis_results.get('languages', ['Unknown']))}\n"
        prompt += f"Frameworks: {', '.join(analysis_results.get('frameworks', ['Unknown']))}\n\n"
        
        # Add sample files
        parsed_files = analysis_results.get('parsed_files', {})
        sample_files = list(parsed_files.keys())[:5]  # Take up to 5 files
        
        prompt += "Sample Files:\n"
        for file_path in sample_files:
            prompt += f"- {file_path}\n"
            
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
        
        return prompt
