"""
Input validation and sanitization utilities for API requests.
"""
from typing import List, Dict, Any
from app.models.schema import GenerateRequest, Constraints

# Validation constants
MIN_QUERY_LENGTH = 5
MAX_QUERY_LENGTH = 2000
MAX_COMPONENTS = 50
MAX_EDGES = 200
MIN_BUDGET = 0
MAX_BUDGET = 1000000
MIN_TEAM_SIZE = 1
MAX_TEAM_SIZE = 10000
MIN_RPS = 0
MAX_RPS = 1000000


def validate_generate_request(req: GenerateRequest) -> tuple[bool, str]:
    """
    Validate incoming GenerateRequest for common issues.
    
    Returns:
        (is_valid, error_message)
    """
    # Validate query length
    if not req.query or len(req.query.strip()) < MIN_QUERY_LENGTH:
        return False, f"Query must be at least {MIN_QUERY_LENGTH} characters long"
    
    if len(req.query) > MAX_QUERY_LENGTH:
        return False, f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters"
    
    # Validate provider
    valid_providers = ["gemini", "ollama", "groq", "openrouter"]
    if req.provider not in valid_providers:
        return False, f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
    
    # Validate existing_components if provided
    if req.existing_components:
        if len(req.existing_components) > MAX_COMPONENTS:
            return False, f"Too many components. Maximum is {MAX_COMPONENTS}"
        
        for comp in req.existing_components:
            if not isinstance(comp, dict) or "name" not in comp or "type" not in comp:
                return False, "Invalid component format. Each must have 'name' and 'type'"
    
    # Validate existing_diagram if provided (refinement mode)
    if req.existing_diagram:
        if not isinstance(req.existing_diagram, dict):
            return False, "existing_diagram must be a dictionary"
        
        edges = req.existing_diagram.get("edges", [])
        if len(edges) > MAX_EDGES:
            return False, f"Too many edges. Maximum is {MAX_EDGES}"
    
    return True, ""


def validate_constraints(constraints: Constraints) -> tuple[bool, str]:
    """
    Validate constraint values are within acceptable ranges.
    
    Returns:
        (is_valid, error_message)
    """
    if constraints.budget_usd_month is not None:
        if constraints.budget_usd_month < MIN_BUDGET or constraints.budget_usd_month > MAX_BUDGET:
            return False, f"Budget must be between ${MIN_BUDGET} and ${MAX_BUDGET}"
    
    if constraints.team_size is not None:
        if constraints.team_size < MIN_TEAM_SIZE or constraints.team_size > MAX_TEAM_SIZE:
            return False, f"Team size must be between {MIN_TEAM_SIZE} and {MAX_TEAM_SIZE}"
    
    if constraints.peak_rps is not None:
        if constraints.peak_rps < MIN_RPS or constraints.peak_rps > MAX_RPS:
            return False, f"Peak RPS must be between {MIN_RPS} and {MAX_RPS}"
    
    if constraints.region:
        if not isinstance(constraints.region, str) or len(constraints.region) > 100:
            return False, "Invalid region format"
    
    return True, ""


def sanitize_query(query: str) -> str:
    """
    Sanitize user query by removing extra whitespace and special characters.
    """
    # Remove extra whitespace
    query = " ".join(query.split())
    
    # Limit to MAX_QUERY_LENGTH
    if len(query) > MAX_QUERY_LENGTH:
        query = query[:MAX_QUERY_LENGTH]
    
    return query.strip()
