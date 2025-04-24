import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid

class VectorStore:
    """Manages vector embeddings storage and retrieval"""
    
    def __init__(self, collection_name: str = "code_embeddings", persist_directory: str = "./data/chroma_db"):
        """Initialize the vector store with ChromaDB"""
        # Ensure the persist directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            chroma_db_impl="duckdb+parquet"
        ))
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"Connected to existing collection: {collection_name}")
        except ValueError:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Code embeddings for microservice migration"}
            )
            print(f"Created new collection: {collection_name}")
    
    async def add_embeddings(self, texts: List[str], embeddings: List[List[float]], 
                           metadata_list: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Add embeddings to the vector store"""
        # Generate IDs if not provided
        ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Ensure metadata is provided for each text
        if metadata_list is None:
            metadata_list = [{} for _ in range(len(texts))]
        
        # Add embeddings to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadata_list,
            ids=ids
        )
        
        return ids
    
    async def search_similar(self, query_embedding: List[float], top_k: int = 5) -> Dict[str, Any]:
        """Search for similar code snippets using vector similarity"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        return results
    
    async def add_code_file(self, file_path: str, file_content: str, 
                          embedding: List[float], metadata: Dict[str, Any]) -> str:
        """Add a code file with its embedding to the vector store"""
        # Generate a unique ID for this file
        file_id = str(uuid.uuid4())
        
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
        
        return file_id
    
    async def get_all_embeddings(self) -> Dict[str, Any]:
        """Get all stored embeddings"""
        return self.collection.get()
    
    def persist(self):
        """Ensure data is persisted to disk"""
        self.client.persist()
