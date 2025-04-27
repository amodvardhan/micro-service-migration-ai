# app/knowledge/vector_store.py
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
import logging
import asyncio
from functools import wraps

from chromadb.errors import NotFoundError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def async_retry(max_retries=3, delay=1):
    """Decorator for async retry logic with exponential backoff"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            current_delay = delay
            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(f"Failed after {max_retries} retries: {str(e)}")
                        raise
                    logger.warning(f"Retry {retries}/{max_retries} after error: {str(e)}")
                    await asyncio.sleep(current_delay)
                    current_delay *= 2  # Exponential backoff
        return wrapper
    return decorator

class VectorStore:
    """Manages vector embeddings storage and retrieval with resilience patterns"""
    
    def __init__(self, collection_name: str = "code_embeddings", 
                persist_directory: str = "./data/chroma_db"):
        """Initialize the vector store with ChromaDB"""
        
        # Ensure the persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=chromadb.Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection with proper error handling
            try:
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Code embeddings for microservice migration"}
                )
                logger.info(f"Connected to collection: {collection_name}")
            except NotFoundError:  # Changed from ValueError
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={"description": "Code embeddings for microservice migration"}
                )
                logger.info(f"Created new collection: {collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
    
    @async_retry(max_retries=3)
    async def add_embeddings(self, texts: List[str], embeddings: List[List[float]], 
                           metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add embeddings to the vector store with retry logic"""
        if not texts or not embeddings:
            logger.warning("Empty texts or embeddings provided")
            return []
            
        if len(texts) != len(embeddings):
            raise ValueError(f"Number of texts ({len(texts)}) does not match number of embeddings ({len(embeddings)})")
        
        # Generate IDs if not provided
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Ensure metadata is provided for each text
        if metadata_list is None:
            metadata_list = [{} for _ in range(len(texts))]
        elif len(metadata_list) != len(texts):
            raise ValueError(f"Number of metadata items ({len(metadata_list)}) does not match number of texts ({len(texts)})")
        
        # Add embeddings to collection
        try:
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadata_list,
                ids=ids
            )
            self.persist()
            logger.info(f"Successfully added {len(texts)} embeddings to collection")
            return ids
        except Exception as e:
            logger.error(f"Error adding embeddings: {str(e)}")
            raise
    
    @async_retry(max_retries=3)
    async def search_similar(self, query_embedding: List[float], 
                           top_k: int = 5, 
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for similar code snippets using vector similarity with metadata filtering"""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            return {
                "ids": results.get("ids", [[]]),
                "documents": results.get("documents", [[]]),
                "metadatas": results.get("metadatas", [[]]),
                "distances": results.get("distances", [[]])
            }
        except Exception as e:
            logger.error(f"Error searching similar vectors: {str(e)}")
            raise
    
    @async_retry(max_retries=3)
    async def add_code_file(self, file_path: str, file_content: str, 
                          embedding: List[float], metadata: Dict[str, Any]) -> str:
        """Add a code file with its embedding to the vector store"""
        # Generate a unique ID for this file
        file_id = str(uuid.uuid4())
        
        try:
            # Add the file embedding
            self.collection.add(
                embeddings=[embedding],
                documents=[file_content],
                metadatas=[{
                    "file_path": file_path,
                    "language": metadata.get("language", "unknown"),
                    "size": metadata.get("size", 0),
                    "type": metadata.get("type", "unknown"),
                    **metadata
                }],
                ids=[file_id]
            )
            
            self.persist()
            logger.info(f"Successfully added file {file_path} with ID {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Error adding code file: {str(e)}")
            raise
    
    async def get_all_embeddings(self) -> Dict[str, Any]:
        """Get all stored embeddings"""
        try:
            return self.collection.get()
        except Exception as e:
            logger.error(f"Error retrieving all embeddings: {str(e)}")
            raise
    
    def persist(self):
        """Ensure data is persisted to disk"""
        try:
            self.client.persist()
            logger.info("Vector store data persisted to disk")
        except Exception as e:
            logger.error(f"Error persisting vector store: {str(e)}")
            raise
