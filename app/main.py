import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from dotenv import load_dotenv

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

# Initialize services and agents
from app.core.llm_service import LLMService
from app.agents.orchestrator import AgentOrchestrator
from app.agents.analyzer import CodeAnalysisAgent
from app.agents.architect import ArchitectAgent
from app.agents.developer import DeveloperAgent

# Create LLM service
llm_service = LLMService(model="gpt-4.1-mini")

# Create agent orchestrator
orchestrator = AgentOrchestrator(llm_service)

# Create and register agents
analyzer = CodeAnalysisAgent(llm_service)
architect = ArchitectAgent(llm_service)
developer = DeveloperAgent(llm_service)

orchestrator.register_agent('analyzer', analyzer)
orchestrator.register_agent('architect', architect)
orchestrator.register_agent('developer', developer)

# Import API routes
from app.api import routes
app.include_router(routes.router)

# Make orchestrator available to routes
routes.orchestrator = orchestrator

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
