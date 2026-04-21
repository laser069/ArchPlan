from beanie import Document, Indexed
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import Field

class ArchHistory(Document):
    # Training Inputs
    query: str
    full_prompt: str  # We save the exact string from get_system_prompt
    provider: str
    model_name: str
    
    # Training Outputs (The "Answer")
    architecture_narrative: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    raw_nodes: List[List[str]] 
    raw_edges: List[List[str]]
    scaling: str = "N/A"
    components: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata for filtering high-quality data
    constraints: Optional[Dict[str, Any]] = None
    is_gold_standard: bool = False 
    user_rating: Optional[int] = None # 1-5
    
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "generation_history"
