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
    
    print(f"\n--- {'Refining' if is_refine else 'New'} Design Request ---")
    print(f"Query: {req.query[:50]}...")

    try:
        extracted_dict = await extract_constraints(req.query)

        if req.constraints:
            explicit = req.constraints.model_dump(exclude_none=True)
            merged = {**extracted_dict, **explicit}
        else:
            merged = extracted_dict

        constraints = Constraints(**merged)

        # Pass existing_diagram to the service
        result = await generate_architecture(
            query=req.query, 
            constraints=constraints,
            existing_diagram=req.existing_diagram
        )
        
        print(f"--- Completed in {time.time() - start_time:.2f}s ---\n")
        return result

    except Exception as e:
        print(f"!!! ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
