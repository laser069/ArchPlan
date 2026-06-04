import time
import traceback
import json
import logging
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

from app.models.schema import GenerateRequest, GenerateResponse, Constraints, Component, User
from app.models.database import ArchHistory  # Added User
from app.auth import get_current_user              # Added Auth Dependency
from app.services.llm_service import generate_architecture, _inflate
from app.services.constraint_extractor import extract_constraints
from app.services.prompts import get_system_prompt, get_refine_prompt
from app.core.validators import validate_constraints

router = APIRouter(tags=["Generation"])

logger = logging.getLogger(__name__)

async def log_to_training_db(req: GenerateRequest, result: GenerateResponse, is_refine: bool, user_email: str):
    """
    Background task to save the generation to MongoDB for future fine-tuning.
    Now includes user_email to link history to the specific user.
    """
    try:
        if is_refine:
            nodes_data = [[c.name, c.type] for c in result.components]
            prompt = get_refine_prompt(
                query=req.query,
                existing_nodes=json.dumps(nodes_data),
                existing_edges=json.dumps(result.raw_edges),
                constraints_data=json.dumps(result.constraints)
            )
        else:
            prompt = get_system_prompt(req.query, json.dumps(result.constraints), context="")

        db_entry = ArchHistory(
            user_email=user_email,  # Link to user
            query=req.query,
            full_prompt=prompt,
            provider=req.provider,
            model_name=req.model or "DEFAULT",
            architecture_narrative=result.architecture,
            nodes=result.nodes,
            edges=result.edges,
            raw_nodes=result.raw_nodes,
            raw_edges=result.raw_edges,
            scaling=result.scaling,
            components=[{"name": c.name, "type": c.type} for c in result.components],
            constraints=result.constraints,
            is_gold_standard=False 
        )
        await db_entry.insert()
        print(f"--- Logged to MongoDB for user: {user_email} ---")
    except Exception:
        logger.exception("log_to_training_db failed")

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(
    req: GenerateRequest, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)  # Protected Route
):
    t0 = time.time()
    is_refine = bool(req.existing_diagram)
    
    provider = req.provider
    model = req.model
    
    log_model = model if model else "DEFAULT"
    print(f"\n--- {'Refining' if is_refine else 'Generating'} for {current_user.email} with {provider.upper()} ---")
    
    try:
        # 1. Handle Constraint Logic
        if is_refine:
            constraints_data = (req.cached_constraints or 
                                (req.constraints.model_dump(exclude_none=True) if req.constraints else {}))
            constraints = Constraints(**constraints_data)
        else:
            extracted = await extract_constraints(req.query)
            user_constraints = req.constraints.model_dump(exclude_none=True) if req.constraints else {}
            merged = {**extracted, **user_constraints}
            constraints = Constraints(**merged)

        is_valid, error_msg = validate_constraints(constraints)
        if not is_valid:
            raise HTTPException(status_code=422, detail=error_msg)

        # 2. Call the Service Layer
        result = await generate_architecture(
            query=req.query,
            provider=provider,
            model=model,
            constraints=constraints,
            existing_diagram=req.existing_diagram,
            existing_components=req.existing_components,
            cached_constraints=req.cached_constraints,
        )

        # 3. Attach constraints for frontend caching
        result = result.model_copy(update={"constraints": constraints.model_dump(exclude_none=True)})

        # 4. Background Tasks - Pass current_user email
        background_tasks.add_task(log_to_training_db, req, result, is_refine, current_user.email)

        print(f"--- Completed in {time.time()-t0:.2f}s ---")
        return result

    except Exception as e:
        print(f"!!! Error in generate_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[GenerateResponse])
async def get_user_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user) # Now only shows YOUR history
):
    try:
        # Pull documents specifically for the logged-in user
        history_docs = await ArchHistory.find(
            ArchHistory.user_email == current_user.email
        ).sort("-id").limit(limit).to_list()
        
        formatted_history = []
        for doc in history_docs:
            components = [
                Component(name=c.get("name", ""), type=c.get("type", "Service"))
                for c in getattr(doc, 'components', []) if isinstance(c, dict)
            ]
            
            formatted_history.append(GenerateResponse(
                architecture=getattr(doc, 'architecture_narrative', "No narrative"),
                nodes=getattr(doc, 'nodes', []),
                edges=getattr(doc, 'edges', []),
                raw_nodes=getattr(doc, 'raw_nodes', []),
                raw_edges=getattr(doc, 'raw_edges', []),
                components=components,
                scaling=getattr(doc, 'scaling', "N/A"),
                constraints=getattr(doc, 'constraints', {})
            ))
            
        return formatted_history
        
    except Exception:
        logger.exception("get_user_history failed")
        return []

@router.get("/test-diagram", response_model=GenerateResponse)
async def test_diagram_endpoint():
    """Remains public for quick UI testing."""
    mock_raw = {
        "n": [
            ["User Interface", "cdn"], ["Load Balancer", "loadbalancer"],
            ["Auth Service", "auth"], ["Core API", "service"],
            ["Primary DB", "postgresql"], ["Redis Cache", "redis"],
            ["Metrics", "monitor"]
        ],
        "e": [
            ["User Interface", "Load Balancer"], ["Load Balancer", "Auth Service"],
            ["Load Balancer", "Core API"], ["Auth Service", "Core API"],
            ["Core API", "Primary DB"], ["Core API", "Redis Cache"],
            ["Core API", "Metrics"], ["Primary DB", "Metrics"]
        ],
        "a": "This is a TEST architecture with descriptive node types.",
        "s": "Horizontal scaling for API, read-replicas for DB."
    }
    inflated = _inflate(mock_raw)
    return GenerateResponse(**inflated)