# schema.py
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

VALID_PROVIDERS = Literal["gemini", "ollama"]
VALID_SCALE   = Literal["startup", "growth", "enterprise"]

class Constraints(BaseModel):
    model_config = {"extra": "ignore"}   # silently drops unknown keys from extractor

    budget_usd_month: Optional[int]  = None
    team_size:        Optional[int]  = None
    peak_rps:         Optional[int]  = None
    cloud_provider:   str            = "AWS"
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
    provider: VALID_PROVIDERS = "gemini"
    constraints:         Optional[Constraints]       = None
    existing_diagram:    Optional[str]               = None
    existing_components: Optional[List[Dict[str, Any]]] = None
    cached_constraints:  Optional[Dict[str, Any]]    = None

class GenerateResponse(BaseModel):
    components:   List[Component]
    architecture: str
    scaling:      str
    diagram:      str
    constraints:  Optional[Dict[str, Any]] = None