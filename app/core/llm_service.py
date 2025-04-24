import os
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMService:
    """Service for interacting with OpenAI's GPT models"""
    
    def __init__(self, model="gpt-4.1-mini"):
        """Initialize the LLM service with the specified model"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
            
        self.model = model
        openai.api_key = self.api_key
        
    async def generate_completion(self, prompt: str, temperature: float = 0.2, 
                                 max_tokens: int = 2000) -> Dict[str, Any]:
        """Generate a completion from the LLM"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an AI assistant specialized in software architecture and code analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.to_dict() if hasattr(response, 'usage') else None
            }
        except Exception as e:
            print(f"Error generating completion: {str(e)}")
            raise
            
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts"""
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=texts
            )
            
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            raise
