# app/knowledge/embedding_manager.py
import os
from typing import List, Dict, Any, Optional, Tuple
import logging
import asyncio
from app.core.llm_service import LLMService
from app.knowledge.vector_store import VectorStore

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class EmbeddingManager:
    """Manages the generation and storage of code embeddings with optimized processing"""
    
    def __init__(self, llm_service: LLMService, vector_store: VectorStore):
        """Initialize with LLM service and vector store"""
        self.llm_service = llm_service
        self.vector_store = vector_store
        self.batch_size = 10  # Default batch size
        self.max_content_length = 8000  # Maximum content length for embedding
    
    async def process_codebase(self, parsed_files: Dict[str, Any]) -> Dict[str, Any]:
        """Process a codebase and store embeddings for all files with optimized batching"""
        results = {
            "processed_files": 0,
            "file_ids": {},
            "errors": [],
            "skipped_files": 0
        }
        
        # Process files in batches to avoid token limits
        file_items = list(parsed_files.items())
        total_files = len(file_items)
        logger.info(f"Starting to process {total_files} files for embeddings")
        
        # Process in batches
        for i in range(0, total_files, self.batch_size):
            batch = file_items[i:i+self.batch_size]
            logger.info(f"Processing batch {i//self.batch_size + 1}/{(total_files + self.batch_size - 1)//self.batch_size}")
            
            try:
                # Prepare texts and metadata for embedding
                texts, metadata_list, file_paths = await self._prepare_batch(batch)
                
                if not texts:
                    logger.info("No valid files in this batch, skipping")
                    continue
                
                # Generate embeddings
                embeddings = await self.llm_service.generate_embeddings(texts)
                
                if not embeddings or len(embeddings) != len(texts):
                    error_msg = f"Embedding generation failed or returned incorrect number of embeddings: expected {len(texts)}, got {len(embeddings) if embeddings else 0}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    continue
                
                # Store embeddings
                file_ids = await self.vector_store.add_embeddings(texts, embeddings, metadata_list)
                
                # Update results
                results["processed_files"] += len(texts)
                for i, file_path in enumerate(file_paths):
                    results["file_ids"][file_path] = file_ids[i]
                
                # Avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                error_msg = f"Error processing batch: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
        
        logger.info(f"Completed processing. Processed {results['processed_files']} files, skipped {results['skipped_files']}, encountered {len(results['errors'])} errors")
        return results
    
    async def _prepare_batch(self, batch: List[Tuple[str, Dict[str, Any]]]) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """Prepare a batch of files for embedding"""
        texts = []
        metadata_list = []
        file_paths = []
        
        for file_path, file_info in batch:
            try:
                # Skip files that are too large or binary
                if file_info.get("size", 0) > 1000000:  # Skip files > 1MB
                    logger.warning(f"File too large, skipping: {file_path}")
                    continue
                
                content = file_info.get("content", "")
                if not content or len(content) < 10:
                    logger.warning(f"Empty or invalid file, skipping: {file_path}")
                    continue
                
                # Truncate content if too long
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length] + "...[truncated]"
                
                # Prepare text for embedding with a prefix to help the model understand context
                text = f"code: {content}"
                texts.append(text)
                
                # Prepare metadata
                extension = file_info.get("extension", "").lstrip(".")
                metadata = {
                    "file_path": file_path,
                    "language": self._get_language_from_extension(extension),
                    "size": file_info.get("size", 0),
                    "extension": extension,
                    "is_truncated": len(content) > self.max_content_length
                }
                metadata_list.append(metadata)
                file_paths.append(file_path)
                
            except Exception as e:
                logger.error(f"Error preparing file {file_path}: {str(e)}")
        
        return texts, metadata_list, file_paths
    
    async def find_similar_code(self, query: str, top_k: int = 5, 
                              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Find code similar to the query with optional metadata filtering"""
        try:
            # Generate embedding for the query
            query_text = f"code: {query}"
            query_embeddings = await self.llm_service.generate_embeddings([query_text])
            
            if not query_embeddings or len(query_embeddings) == 0:
                logger.error("Failed to generate query embedding")
                return {"error": "Failed to generate query embedding"}
            
            # Search for similar code
            query_embedding = query_embeddings[0]
            results = await self.vector_store.search_similar(query_embedding, top_k, filters)
            
            # Format results for better usability
            formatted_results = []
            if results.get("ids") and results["ids"][0]:
                for i, (doc_id, doc, metadata, distance) in enumerate(zip(
                    results["ids"][0], 
                    results["documents"][0], 
                    results["metadatas"][0], 
                    results["distances"][0]
                )):
                    formatted_results.append({
                        "id": doc_id,
                        "content": doc,
                        "metadata": metadata,
                        "similarity": 1.0 - distance  # Convert distance to similarity score
                    })
            
            return {
                "query": query,
                "results": formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error finding similar code: {str(e)}")
            return {"error": str(e)}
    
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
    
    async def chunk_and_embed_large_file(self, file_path: str, content: str, 
                                       metadata: Dict[str, Any]) -> List[str]:
        """Chunk large files and embed each chunk separately"""
        # Calculate optimal chunk size (aim for ~2000 tokens per chunk with overlap)
        chunk_size = 6000  # Approximate characters for 2000 tokens
        overlap = 1000     # Overlap between chunks
        
        if len(content) <= chunk_size:
            # File is small enough to embed as a single chunk
            embedding = await self.llm_service.generate_embeddings([f"code: {content}"])
            file_id = await self.vector_store.add_code_file(
                file_path, 
                content, 
                embedding[0], 
                {**metadata, "chunk_index": 0, "total_chunks": 1}
            )
            return [file_id]
        
        # For larger files, chunk the content
        chunk_ids = []
        chunks = []
        
        # Create overlapping chunks
        for i in range(0, len(content), chunk_size - overlap):
            chunk = content[i:i + chunk_size]
            if len(chunk) < 100:  # Skip very small chunks
                continue
            chunks.append(chunk)
        
        # Embed each chunk
        for i, chunk in enumerate(chunks):
            chunk_text = f"code: {chunk} (chunk {i+1} of {len(chunks)} from {file_path})"
            embedding = await self.llm_service.generate_embeddings([chunk_text])
            
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "is_chunk": True
            }
            
            chunk_id = await self.vector_store.add_code_file(
                file_path, 
                chunk, 
                embedding[0], 
                chunk_metadata
            )
            chunk_ids.append(chunk_id)
        
        return chunk_ids
