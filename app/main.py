import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from dotenv import load_dotenv
import logging

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

# Dependency provider for orchestrator
from functools import lru_cache
from app.core.llm_service import LLMService
from app.knowledge.vector_store import VectorStore
from app.knowledge.embedding_manager import EmbeddingManager
from app.agents.orchestrator import AgentOrchestrator
from app.agents.analyzer import CodeAnalysisAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent

@lru_cache()
def get_orchestrator():
    logger.info("Initializing orchestrator (singleton)")
    llm_service = LLMService(model="gpt-4.1-mini")
    vector_store = VectorStore(collection_name="code_embeddings", persist_directory="./data/chroma_db")
    embedding_manager = EmbeddingManager(llm_service, vector_store)
    orchestrator = AgentOrchestrator(llm_service)
    analyzer = CodeAnalysisAgent(llm_service, embedding_manager)
    architect = ArchitectAgent(llm_service)
    developer = DeveloperAgent(llm_service)
    orchestrator.register_agent('analyzer', analyzer)
    orchestrator.register_agent('architect', architect)
    orchestrator.register_agent('developer', developer)
    return orchestrator

# Import API routes after get_orchestrator is defined
from app.api import routes
app.include_router(routes.router)

# Serve static files (React build)
static_dir = Path("static/dist")
logger.info(f"Checking for static files in {static_dir}")
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static_root")
    logger.info(f"Static files mounted from {static_dir}")
else:
    logger.warning(f"Directory {static_dir} does not exist. Static files will not be served.")

# SPA fallback for unknown routes (optional if using html=True above)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    logger.info(f"Serving SPA for path: {full_path}")
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        logger.error(f"File {index_path} does not exist")
        raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
