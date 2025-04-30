from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import uuid
import datetime
import logging
from app.models.SearchRequestModel import SearchRequest
from app.main import get_orchestrator
from app.agents.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for analysis results
analysis_results_store = {}

class RepositoryRequest(BaseModel):
    repo_url: str

@router.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/api/analyze")
async def analyze_repository(
    request: RepositoryRequest,
    background_tasks: BackgroundTasks,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    repo_id = str(uuid.uuid4())
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
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_data = analysis_results_store[repo_id]

    if analysis_data["status"] == "processing":
        return {
            "repo_id": repo_id,
            "status": "processing",
            "message": "Analysis is still in progress"
        }

    if analysis_data["status"] == "failed":
        return {
            "repo_id": repo_id,
            "status": "failed",
            "error": analysis_data.get("error", "Unknown error")
        }

    results = analysis_data.get("results", {})

    # Find the analyzer and architect results by scanning for their keys
    analyzer_result = None
    architect_result = None
    for k, v in results.items():
        if k.startswith("analyzer_analyze_repository"):
            analyzer_result = v.get("analysis_results", v)
        if k.startswith("architect_identify_service_boundaries"):
            architect_result = v

    # Fallbacks
    if not analyzer_result:
        analyzer_result = results.get("analysis_results", {})
    if not architect_result:
        architect_result = {}

    def merged_field(field, default=[]):
        # For potential_services/service_boundaries, check both field names
        if field == "potential_services":
            return (
                architect_result.get("service_boundaries")
                or analyzer_result.get("potential_services", default)
            )
        return (
            architect_result.get(field)
            if architect_result.get(field)
            else analyzer_result.get(field, default)
        )

    return {
        "repo_id": repo_id,
        "repo_url": analysis_data["repo_url"],
        "status": "completed",
        "timestamp": analysis_data["timestamp"],
        "analysis": {
            "architecture_type": architect_result.get("architecture_type")
                or analyzer_result.get("architecture_type", "Unknown"),
            "potential_services": merged_field("potential_services", []),
            "entities": merged_field("entities", []),
            "api_endpoints": merged_field("api_endpoints", []),
            "dependencies": merged_field("dependencies", []),
            "semantic_insights": merged_field("semantic_insights", {}),
        }
    }




@router.get("/api/analyses")
async def list_analyses():
    analyses = []
    for repo_id, data in analysis_results_store.items():
        analyses.append({
            "repo_id": repo_id,
            "repo_url": data["repo_url"],
            "status": data["status"],
            "timestamp": data["timestamp"]
        })
    analyses.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"analyses": analyses}

@router.post("/api/search")
async def search_code(
    request: SearchRequest,
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
):
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
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    analysis_data = analysis_results_store[repo_id]
    if analysis_data["status"] != "completed":
        return {
            "repo_id": repo_id,
            "status": analysis_data["status"],
            "message": "Analysis is not complete"
        }
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
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    analysis_data = analysis_results_store[repo_id]
    if analysis_data["status"] != "completed":
        return {
            "repo_id": repo_id,
            "status": analysis_data["status"],
            "message": "Analysis is not complete"
        }
    results = analysis_data.get("results", {})
    analysis_results = results.get("analysis_results", {})
    dependencies = analysis_results.get("dependencies", [])
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
    if repo_id not in analysis_results_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    analysis_data = analysis_results_store[repo_id]
    if analysis_data["status"] != "completed":
        return {
            "repo_id": repo_id,
            "status": analysis_data["status"],
            "message": "Analysis is not complete"
        }
    results = analysis_data.get("results", {})
    analysis_results = results.get("analysis_results", {})
    entities = analysis_results.get("entities", [])
    return {
        "repo_id": repo_id,
        "repo_url": analysis_data["repo_url"],
        "entities": entities
    }
