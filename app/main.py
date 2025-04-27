import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv
from app.knowledge.vector_store import VectorStore
from app.knowledge.embedding_manager import EmbeddingManager

import logging
# Initialize services and agents
from app.core.llm_service import LLMService
from app.agents.orchestrator import AgentOrchestrator
from app.agents.analyzer import CodeAnalysisAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.core.code_analyzer import CodeAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Microservice Migration AI",
    description="An AI-powered tool for migrating monolithic applications to microservices",
    version="0.1.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")



# Create LLM service
logger.info("Initializing application services")
llm_service = LLMService(model="gpt-4.1-mini")

# Initialize vector store
logger.info("Initializing vector database")
vector_store = VectorStore(collection_name="code_embeddings", persist_directory="./data/chroma_db")

# Initialize embedding manager
logger.info("Initializing embedding manager")
embedding_manager = EmbeddingManager(llm_service, vector_store)

# Create agent orchestrator
logger.info("Creating agent orchestrator")
orchestrator = AgentOrchestrator(llm_service)

# Create and register agents
logger.info("Initializing and registering AI agents")
analyzer = CodeAnalysisAgent(llm_service, embedding_manager)
architect = ArchitectAgent(llm_service)
developer = DeveloperAgent(llm_service)

orchestrator.register_agent('analyzer', analyzer)
orchestrator.register_agent('architect', architect)
orchestrator.register_agent('developer', developer)
logger.info("Application initialization complete")

# Import API routes
from app.api import routes
app.include_router(routes.router)

# Make orchestrator available to routes
routes.orchestrator = orchestrator

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
