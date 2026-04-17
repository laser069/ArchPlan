import time
import traceback
from fastapi import APIRouter, HTTPException
from app.models.schema import GenerateRequest, GenerateResponse, Constraints
from app.services.llm_service import generate_architecture
from app.services.constraint_extractor import extract_constraints
from app.services.llm_service import _inflate

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(req: GenerateRequest):
    t0 = time.time()
    is_refine = bool(req.existing_diagram)
    
    # 1. Determine the provider and model. 
    # Pull 'provider' and 'model' directly from the request object.
    provider = getattr(req, "provider", "groq")
    model = getattr(req, "model", None) # Dynamic model from frontend
    
    log_model = model if model else "DEFAULT"
    print(f"\n--- {'Refining' if is_refine else 'Generating'} with {provider.upper()} ({log_model}) ---")
    print(f"Query: {req.query[:50]}...")
    
    try:
        # 2. Handle Constraint Logic
        if is_refine:
            # If refining, use cached constraints to maintain consistency across iterations
            constraints_data = (req.cached_constraints or 
                                (req.constraints.model_dump(exclude_none=True) if req.constraints else {}))
            constraints = Constraints(**constraints_data)
        else:
            # If new, extract constraints from the natural language query
            extracted = await extract_constraints(req.query)
            # Merge extracted constraints with any explicit ones provided in the request
            user_constraints = req.constraints.model_dump(exclude_none=True) if req.constraints else {}
            merged = {**extracted, **user_constraints}
            constraints = Constraints(**merged)

        # 3. Call the Service Layer
        # Now passing the 'model' parameter to support dynamic LLM selection
        result = await generate_architecture(
            query=req.query,
            provider=provider,
            model=model, # Pass dynamic selection here
            constraints=constraints,
            existing_diagram=req.existing_diagram,
            existing_components=req.existing_components,
            cached_constraints=req.cached_constraints,
        )

        # 4. Attach constraints to the result for frontend caching
        if not is_refine:
            result = result.model_copy(update={"constraints": constraints.model_dump(exclude_none=True)})

        print(f"--- Completed in {time.time()-t0:.2f}s ---")
        return result

    except Exception as e:
        print(f"!!! Error in generate_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/test-diagram", response_model=GenerateResponse)
async def test_diagram_endpoint():
    """Returns a hardcoded architectural JSON to test frontend rendering."""
    mock_raw = {
        "n": [
            ["User Interface", "X"], 
            ["Load Balancer", "L"], 
            ["Core API", "S"], 
            ["Primary DB", "D"],
            ["Redis Cache", "C"]
        ],
        "e": [
            ["User Interface", "Load Balancer"],
            ["Load Balancer", "Core API"],
            ["Core API", "Primary DB"],
            ["Core API", "Redis Cache"]
        ],
        "a": "This is a TEST architecture. No LLM tokens were harmed.",
        "s": "Horizontal scaling for API, Read-replicas for DB."
    }
    
    # Process the mock data through our new JSON inflator
    inflated = _inflate(mock_raw)
    return GenerateResponse(**inflated)