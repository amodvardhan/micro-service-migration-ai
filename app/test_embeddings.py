# Create a test_embeddings.py file in the root directory
import asyncio
import os
from dotenv import load_dotenv
import logging
from app.core.llm_service import LLMService
from app.knowledge.vector_store import VectorStore
from app.knowledge.embedding_manager import EmbeddingManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_embeddings():
    """Test embedding generation and storage"""
    logger.info("Starting embedding test")
    
    # Initialize services
    llm_service = LLMService(model="gpt-4.1-mini")
    vector_store = VectorStore(collection_name="test_embeddings", persist_directory="./data/test_chroma_db")
    embedding_manager = EmbeddingManager(llm_service, vector_store)
    
    # Sample code snippets
    code_snippets = [
        "def hello_world():\n    print('Hello, World!')",
        "class User:\n    def __init__(self, name):\n        self.name = name",
        "async function fetchData() {\n    const response = await fetch('/api/data');\n    return response.json();\n}"
    ]
    
    # Generate embeddings
    logger.info("Generating embeddings for sample code snippets")
    embeddings = await llm_service.generate_embeddings(code_snippets)
    
    # Store embeddings
    metadata_list = [
        {"language": "Python", "type": "function"},
        {"language": "Python", "type": "class"},
        {"language": "JavaScript", "type": "function"}
    ]
    
    logger.info("Storing embeddings in vector database")
    ids = await vector_store.add_embeddings(code_snippets, embeddings, metadata_list)
    logger.info(f"Stored {len(ids)} embeddings with IDs: {ids}")
    
    # Test search
    logger.info("Testing semantic search functionality")
    query = "a function that prints a greeting message"
    query_embeddings = await llm_service.generate_embeddings([query])
    results = await vector_store.search_similar(query_embeddings[0], top_k=2)
    
    logger.info("\nSearch Results:")
    for i, (doc, score) in enumerate(zip(results['documents'][0], results['distances'][0])):
        logger.info(f"{i+1}. Score: {score:.4f}")
        logger.info(f"Code: {doc[:100]}...")
        logger.info("")
    
    # Test filtering
    logger.info("Testing search with metadata filtering")
    filter_results = await vector_store.search_similar(
        query_embeddings[0], 
        top_k=2,
        filters={"language": "Python"}
    )
    
    logger.info("\nFiltered Search Results (Python only):")
    for i, (doc, metadata) in enumerate(zip(filter_results['documents'][0], filter_results['metadatas'][0])):
        logger.info(f"{i+1}. Language: {metadata['language']}")
        logger.info(f"Code: {doc[:100]}...")
        logger.info("")
    
    logger.info("Embedding test completed successfully")

if __name__ == "__main__":
    asyncio.run(test_embeddings())
