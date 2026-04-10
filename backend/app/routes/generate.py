# router.py
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
    print(f"\n--- {'Refine' if is_refine else 'New'} | {req.query[:50]} ---")
    try:
        if is_refine:
            constraints = Constraints(**(req.cached_constraints or
                (req.constraints.model_dump(exclude_none=True) if req.constraints else {})))
        else:
            extracted = await extract_constraints(req.query)
            merged = {**extracted, **(req.constraints.model_dump(exclude_none=True) if req.constraints else {})}
            constraints = Constraints(**merged)

        result = await generate_architecture(
            query=req.query,
            provider=getattr(req, "provider", "gemini"),
            constraints=constraints,
            existing_diagram=req.existing_diagram,
            existing_components=req.existing_components,
            cached_constraints=req.cached_constraints,
        )
        if not is_refine:
            result = result.model_copy(update={"constraints": constraints.model_dump(exclude_none=True)})

        print(f"--- Done in {time.time()-t0:.2f}s ---")
        return result
    except Exception as e:
        print(f"!!! {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))