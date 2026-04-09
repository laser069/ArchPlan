from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any

class Constraints(BaseModel):
    budget_usd_month: int | None = None
    team_size: int | None = None
    peak_rps: int | None = None
    cloud_provider: str = "AWS"
    region: str | None = None
    stack: List[str] = Field(default_factory=list)
    avoid: List[str] = Field(default_factory=list)
    compliance: List[str] = Field(default_factory=list)
    scale_level: Literal["startup", "growth", "enterprise"] = "startup"

class Component(BaseModel):
    name: str
    type: str

class GenerateRequest(BaseModel):
    query: str
    # Added: Support for choosing the LLM provider
    provider: Literal["gemini", "ollama"] = "gemini"
    constraints: Optional[Constraints] = None
    existing_diagram: Optional[str] = None
    # Added: Pass back previous components so the LLM keeps names consistent
    existing_components: Optional[List[Dict[str, Any]]] = None
    cached_constraints: Optional[Dict[str, Any]] = None

class GenerateResponse(BaseModel):
    components: List[Component]
    architecture: str
    scaling: str
    diagram: str
    # Changed to Any/Dict to ensure the frontend can easily store/return it
    constraints: Optional[Dict[str, Any]] = None