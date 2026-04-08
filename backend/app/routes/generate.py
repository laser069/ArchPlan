from fastapi import APIRouter, HTTPException
from app.models.schema import GenerateRequest, GenerateResponse, Constraints
from app.services.llm_service import generate_architecture
from app.services.constraint_extractor import extract_constraints
import time

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(req: GenerateRequest):
    start_time = time.time()
    is_refine = bool(req.existing_diagram)

    print(f"\n--- {'Refining (FAST PATH)' if is_refine else 'New Design'} Request ---")
    print(f"Query: {req.query[:50]}...")

    try:
        if is_refine:
            cached = req.cached_constraints or (
                req.constraints.model_dump(exclude_none=True) if req.constraints else {}
            )
            constraints = Constraints(**cached)
        else:
            extracted_dict = await extract_constraints(req.query)
            if req.constraints:
                explicit = req.constraints.model_dump(exclude_none=True)
                merged = {**extracted_dict, **explicit}
            else:
                merged = extracted_dict
            constraints = Constraints(**merged)

        result = await generate_architecture(
            query=req.query,
            constraints=constraints,
            existing_diagram=req.existing_diagram,
            existing_components=None,
            cached_constraints=req.cached_constraints,
        )

        # Echo constraints back to frontend for caching (new designs only)
        if not is_refine:
            result.constraints = constraints.model_dump(exclude_none=True)

        elapsed = time.time() - start_time
        print(f"--- Completed in {elapsed:.2f}s {'(fast refine)' if is_refine else '(full generate)'} ---\n")
        return result

    except Exception as e:
        print(f"!!! ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))