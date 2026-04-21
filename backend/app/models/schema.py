from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

VALID_PROVIDERS = Literal["gemini", "ollama", "groq", "openrouter"]
VALID_SCALE   = Literal["startup", "growth", "enterprise"]

class Constraints(BaseModel):
    model_config = ConfigDict(extra="ignore")
    budget_usd_month: Optional[int]  = None
    team_size:         Optional[int]  = None
    peak_rps:          Optional[int]  = None
    cloud_provider:   str             = "AWS"
    region:           Optional[str]  = None
    stack:      List[str] = Field(default_factory=list)
    avoid:      List[str] = Field(default_factory=list)
    compliance: List[str] = Field(default_factory=list)
    scale_level: VALID_SCALE = "startup"

class Component(BaseModel):
    """Represents an architectural component with name and type."""
    name: str
    type: str  # Maps to TYPE_MAP values like "Service", "Gateway", etc.

class GenerateRequest(BaseModel):
    """Request model for architecture generation endpoint."""
    query:    str
    provider: VALID_PROVIDERS = "groq"
    model:    Optional[str] = None 
    constraints:         Optional[Constraints]       = None
    # existing_diagram is the complete diagram state including nodes and edges
    existing_diagram:    Optional[Dict[str, Any]]     = None 
    existing_components: Optional[List[Dict[str, Any]]] = None
    cached_constraints:  Optional[Dict[str, Any]]    = None

class GenerateResponse(BaseModel):
    """Response model for architecture generation."""
    components:   List[Component]
    architecture: str
    scaling:      str
    nodes:        List[Dict[str, Any]]
    edges:        List[Dict[str, Any]]
    raw_nodes:    List[List[str]] 
    raw_edges:    List[List[str]]
    constraints:  Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="allow")
