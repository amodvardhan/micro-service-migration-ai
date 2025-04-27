from typing import Any, Dict
from git import Optional
from pydantic import BaseModel


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None