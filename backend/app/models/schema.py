from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

VALID_PROVIDERS = Literal["gemini", "ollama", "groq", "openrouter"]
VALID_SCALE   = Literal["startup", "growth", "enterprise"]

class Constraints(BaseModel):
    model_config = {"extra": "ignore"}
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
    name: str
    type: str

class GenerateRequest(BaseModel):
    query:    str
    provider: VALID_PROVIDERS = "groq"
    model:    Optional[str] = None 
    constraints:         Optional[Constraints]       = None
    # CHANGED: existing_diagram is now a Dict (the JSON state) instead of a str
    existing_diagram:    Optional[Dict[str, Any]]     = None 
    existing_components: Optional[List[Dict[str, Any]]] = None
    cached_constraints:  Optional[Dict[str, Any]]    = None

class GenerateResponse(BaseModel):
    components:   List[Component]
    architecture: str
    scaling:      str
    # CHANGED: Replaced diagram: str with nodes and edges
    nodes:        List[Dict[str, Any]]
    edges:        List[Dict[str, Any]]
    # CRITICAL: Keep these for the refinement loop logic
    raw_nodes:    List[List[str]] 
    raw_edges:    List[List[str]]
    constraints:  Optional[Dict[str, Any]] = None