# app/main.py
import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

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

# Initialize services and agents
from app.core.llm_service import LLMService
from app.knowledge.vector_store import VectorStore
from app.knowledge.embedding_manager import EmbeddingManager
from app.agents.orchestrator import AgentOrchestrator
from app.agents.analyzer import CodeAnalysisAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent
from app.core.code_analyzer import CodeAnalyzer

# Create a dependency to provide the orchestrator to routes
def get_orchestrator():
    return orchestrator

# Now import the API routes
from app.api import routes
app.include_router(routes.router)

# Mount static files if the directory exists
static_dir = Path("static/dist")
logger.info(f"Checking for static files in {static_dir}")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Static files mounted from {static_dir}")
else:
    logger.warning(f"Directory {static_dir} does not exist. Static files will not be served.")

# Add a catch-all route for the SPA (after the API routes)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    logger.info(f"Serving SPA for path: {full_path}")
    # Skip API routes - they should be handled by the router above
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Serve the index.html for any other route
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        logger.error(f"File {index_path} does not exist")
        raise HTTPException(status_code=404, detail="Frontend not built")
    
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



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
