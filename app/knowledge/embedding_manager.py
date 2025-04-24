# Create app/knowledge/embedding_manager.py
import os
from typing import List, Dict, Any, Optional
from app.core.llm_service import LLMService
from app.knowledge.vector_store import VectorStore

class EmbeddingManager:
    """Manages the generation and storage of code embeddings"""
    
    def __init__(self, llm_service: LLMService, vector_store: VectorStore):
        """Initialize with LLM service and vector store"""
        self.llm_service = llm_service
        self.vector_store = vector_store
    
    async def process_codebase(self, parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        """Process a codebase and store embeddings for all files"""
        results = {
            "processed_files": 0,
            "file_ids": {},
            "errors": []
        }
        
        # Process files in batches to avoid token limits
        batch_size = 10
        file_items = list(parsed_files.items())
        
        for i in range(0, len(file_items), batch_size):
            batch = file_items[i:i+batch_size]
            
            try:
                # Prepare texts and metadata for embedding
                texts = []
                metadata_list = []
                file_paths = []
                
                for file_path, file_info in batch:
                    # Skip files that are too large or binary
                    if file_info.get("size", 0) > 1000000:  # Skip files > 1MB
                        results["errors"].append(f"File too large: {file_path}")
                        continue
                    
                    content = file_info.get("content", "")
                    if not content or len(content) < 10:
                        results["errors"].append(f"Empty or invalid file: {file_path}")
                        continue
                    
                    # Prepare text for embedding with a prefix to help the model understand context
                    text = f"code: {content}"
                    texts.append(text)
                    
                    # Prepare metadata
                    extension = file_info.get("extension", "").lstrip(".")
                    metadata = {
                        "file_path": file_path,
                        "language": self._get_language_from_extension(extension),
                        "size": file_info.get("size", 0),
                        "extension": extension
                    }
                    metadata_list.append(metadata)
                    file_paths.append(file_path)
                
                if not texts:
                    continue
                
                # Generate embeddings
                embeddings = await self.llm_service.generate_embeddings(texts)
                
                # Store embeddings
                file_ids = await self.vector_store.add_embeddings(texts, embeddings, metadata_list)
                
                # Update results
                results["processed_files"] += len(texts)
                for i, file_path in enumerate(file_paths):
                    results["file_ids"][file_path] = file_ids[i]
                
            except Exception as e:
                results["errors"].append(f"Error processing batch: {str(e)}")
        
        # Persist changes
        self.vector_store.persist()
        
        return results
    
    async def find_similar_code(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Find code similar to the query"""
        # Generate embedding for the query
        query_text = f"code: {query}"
        query_embeddings = await self.llm_service.generate_embeddings([query_text])
        
        if not query_embeddings or len(query_embeddings) == 0:
            return {"error": "Failed to generate query embedding"}
        
        # Search for similar code
        query_embedding = query_embeddings[0]
        results = await self.vector_store.search_similar(query_embedding, top_k)
        
        return results
    
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
