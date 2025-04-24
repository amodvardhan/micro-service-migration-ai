from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# This will be set by the main application
orchestrator = None

class RepositoryRequest(BaseModel):
    repo_url: str

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.post("/api/analyze")
async def analyze_repository(request: RepositoryRequest, background_tasks: BackgroundTasks):
    """Analyze a repository"""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
        
    # Start analysis in the background
    # Note: In a real application, you would use a more robust task queue
    background_tasks.add_task(orchestrator.process_codebase, request.repo_url)
    
    return {"status": "Analysis started", "repo_url": request.repo_url}
