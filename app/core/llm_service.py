import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

class LLMService:
    """Service for interacting with OpenAI's GPT models asynchronously"""

    #gpt-4o 
    def __init__(self, model: str = "gpt-4.1-nano"):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.model = os.getenv("OPENAI_DEFAULT_MODEL", model)
        self.aclient = AsyncOpenAI(api_key=self.api_key)

    async def generate_completion(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """Generate a completion from the LLM"""
        try:
            response = await self.aclient.chat.completions.create(
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
                "usage": response.usage.model_dump() if hasattr(response, 'usage') else None
            }
        except Exception as e:
            print(f"Error generating completion: {str(e)}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = os.getenv("EMBEDDING_TEXT_DEFAULT_MODEL") 
    ) -> List[List[float]]:
        """Generate embeddings for the given texts"""
        try:
            response = await self.aclient.embeddings.create(
                model=model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            raise
