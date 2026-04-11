import time
import traceback
from fastapi import APIRouter, HTTPException
from app.models.schema import GenerateRequest, GenerateResponse, Constraints
from app.services.llm_service import generate_architecture
from app.services.constraint_extractor import extract_constraints

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(req: GenerateRequest):
    t0 = time.time()
    is_refine = bool(req.existing_diagram)
    
    # 1. Determine the provider. 
    # We default to "groq" for the best speed/reasoning balance on the free tier.
    provider = getattr(req, "provider", "groq")
    
    print(f"\n--- {'Refining' if is_refine else 'Generating'} with {provider.upper()} | {req.query[:50]} ---")
    
    try:
        # 2. Handle Constraint Logic
        if is_refine:
            # If refining, use cached constraints or existing ones to maintain consistency
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
        result = await generate_architecture(
            query=req.query,
            provider=provider,
            constraints=constraints,
            existing_diagram=req.existing_diagram,
            existing_components=req.existing_components,
            cached_constraints=req.cached_constraints,
        )

        # 4. Attach constraints to the result so the frontend can cache them for refinement
        if not is_refine:
            result = result.model_copy(update={"constraints": constraints.model_dump(exclude_none=True)})

        print(f"--- Completed in {time.time()-t0:.2f}s ---")
        return result

    except Exception as e:
        print(f"!!! Error in generate_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))