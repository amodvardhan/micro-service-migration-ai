# app/api/routes.py
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import uuid
import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# This will be set by the main application
orchestrator = None

# In-memory storage for analysis results
# In a production app, you'd use a proper database
analysis_results_store = {}

class RepositoryRequest(BaseModel):
    repo_url: str

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

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
    
    repo_id = str(uuid.uuid4())  # Generate a unique ID for this analysis
    
    # Start analysis in the background and store results
    async def process_and_store():
        try:
            results = await orchestrator.process_codebase(request.repo_url)
            analysis_results_store[repo_id] = {
                "repo_url": request.repo_url,
                "status": "completed",
                "timestamp": datetime.datetime.now().isoformat(),
                "results": results
            }
            logger.info(f"Analysis completed for repository: {request.repo_url}")
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            analysis_results_store[repo_id] = {
                "repo_url": request.repo_url,
                "status": "failed",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            }
    
    # Store initial status
    analysis_results_store[repo_id] = {
        "repo_url": request.repo_url,
        "status": "processing",
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    logger.info(f"Starting analysis for repository: {request.repo_url}")
    background_tasks.add_task(process_and_store)
    
    return {"status": "Analysis started", "repo_url": request.repo_url, "repo_id": repo_id}

@router.get("/api/analysis/{repo_id}")
async def get_analysis_results(repo_id: str):
    """Get dynamic analysis results for a repository"""
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_results_store[repo_id]
    
    # If analysis is still processing, return status
    if analysis_data["status"] == "processing":
        return {
            "repo_id": repo_id,
            "status": "processing",
            "message": "Analysis is still in progress"
        }
    
    # If analysis failed, return error
    if analysis_data["status"] == "failed":
        return {
            "repo_id": repo_id,
            "status": "failed",
            "error": analysis_data.get("error", "Unknown error")
        }
    
    # If analysis completed, extract and return relevant information
    results = analysis_data.get("results", {})
    analysis_results = results.get("analysis_results", {})
    
    return {
        "repo_id": repo_id,
        "repo_url": analysis_data["repo_url"],
        "status": "completed",
        "timestamp": analysis_data["timestamp"],
        "analysis": {
            "architecture_type": analysis_results.get("architecture_type", "Unknown"),
            "potential_services": analysis_results.get("potential_services", []),
            "entities": [
                {
                    "name": entity.get("name"),
                    "type": entity.get("type"),
                    "namespace": entity.get("namespace")
                } 
                for entity in analysis_results.get("entities", [])[:20]  # Limit to 20 for response size
            ],
            "api_endpoints": analysis_results.get("api_endpoints", []),
            "dependencies": analysis_results.get("dependencies", []),
            "semantic_insights": analysis_results.get("semantic_insights", {})
        }
    }

@router.get("/api/analyses")
async def list_analyses():
    """List all repository analyses"""
    analyses = []
    for repo_id, data in analysis_results_store.items():
        analyses.append({
            "repo_id": repo_id,
            "repo_url": data["repo_url"],
            "status": data["status"],
            "timestamp": data["timestamp"]
        })
    
    # Sort by timestamp (newest first)
    analyses.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return {"analyses": analyses}

@router.post("/api/search")
async def search_code(request: SearchRequest):
    """Search for code semantically"""
    logger.info(f"Semantic code search request: {request.query[:50]}...")
    
    if not orchestrator or not hasattr(orchestrator.agents.get('analyzer', {}), 'embedding_manager'):
        logger.error("Embedding manager not initialized")
        raise HTTPException(status_code=500, detail="Embedding manager not initialized")
    
    try:
        embedding_manager = orchestrator.agents['analyzer'].embedding_manager
        results = await embedding_manager.find_similar_code(
            request.query, 
            request.top_k,
            request.filters
        )
        
        logger.info(f"Search completed, found {len(results.get('results', []))} results")
        return results
    except Exception as e:
        logger.error(f"Error during semantic search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/services/{repo_id}")
async def get_service_boundaries(repo_id: str):
    """Get service boundaries for a repository"""
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_results_store[repo_id]
    
    # If analysis is still processing or failed, return appropriate status
    if analysis_data["status"] != "completed":
        return {
            "repo_id": repo_id,
            "status": analysis_data["status"],
            "message": "Analysis is not complete"
        }
    
    # Extract service boundaries from analysis results
    results = analysis_data.get("results", {})
    analysis_results = results.get("analysis_results", {})
    potential_services = analysis_results.get("potential_services", [])
    
    return {
        "repo_id": repo_id,
        "repo_url": analysis_data["repo_url"],
        "services": potential_services
    }

@router.get("/api/dependencies/{repo_id}")
async def get_service_dependencies(repo_id: str):
    """Get service dependencies for a repository"""
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_results_store[repo_id]
    
    # If analysis is still processing or failed, return appropriate status
    if analysis_data["status"] != "completed":
        return {
            "repo_id": repo_id,
            "status": analysis_data["status"],
            "message": "Analysis is not complete"
        }
    
    # Extract dependencies from analysis results
    results = analysis_data.get("results", {})
    analysis_results = results.get("analysis_results", {})
    dependencies = analysis_results.get("dependencies", [])
    
    # Group dependencies by service
    service_dependencies = {}
    for dependency in dependencies:
        source = dependency.get("source", "Unknown")
        target = dependency.get("target", "Unknown")
        
        if source not in service_dependencies:
            service_dependencies[source] = []
        
        service_dependencies[source].append({
            "target": target,
            "type": dependency.get("type", "Unknown"),
            "description": dependency.get("description", "")
        })
    
    return {
        "repo_id": repo_id,
        "repo_url": analysis_data["repo_url"],
        "service_dependencies": service_dependencies
    }

@router.get("/api/entities/{repo_id}")
async def get_entities(repo_id: str):
    """Get entities for a repository"""
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis_data = analysis_results_store[repo_id]
    
    # If analysis is still processing or failed, return appropriate status
    if analysis_data["status"] != "completed":
        return {
            "repo_id": repo_id,
            "status": analysis_data["status"],
            "message": "Analysis is not complete"
        }
    
    # Extract entities from analysis results
    results = analysis_data.get("results", {})
    analysis_results = results.get("analysis_results", {})
    entities = analysis_results.get("entities", [])
    
    return {
        "repo_id": repo_id,
        "repo_url": analysis_data["repo_url"],
        "entities": entities
    }
