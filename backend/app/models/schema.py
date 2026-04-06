from pydantic import BaseModel
from typing import List

class GenerateRequest(BaseModel):
    query: str

class GenerateResponse(BaseModel):
    components: List[str]
    architecture: str
    scaling: str
    diagram: str
