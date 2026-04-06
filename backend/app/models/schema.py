from pydantic import BaseModel
from typing import List

class Component(BaseModel):
    name: str
    type: str

class GenerateRequest(BaseModel):
    query: str

class GenerateResponse(BaseModel):
    components: List[Component]  
    architecture: str
    scaling: str
    diagram: str