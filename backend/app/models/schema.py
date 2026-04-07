from pydantic import BaseModel, Field
from typing import List, Literal, Optional

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
    constraints: Constraints | None = None
    # This is the "Context Bridge" for the refinement loop
    existing_diagram: Optional[str] = None 

class GenerateResponse(BaseModel):
    components: List[Component]
    architecture: str
    scaling: str
    diagram: str