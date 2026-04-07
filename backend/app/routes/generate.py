from fastapi import APIRouter, HTTPException
from app.models.schema import GenerateRequest, GenerateResponse, Constraints
from app.services.llm_service import generate_architecture
from app.services.constraint_extractor import extract_constraints
import time

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate_endpoint(req: GenerateRequest):
    start_time = time.time()
    print(f"\n--- New Request Received ---")
    print(f"Query: {req.query[:50]}...")

    try:
        # Step 1: Extract constraints using the LLM Extractor
        print("[1/3] Extracting constraints...")
        extracted_dict = await extract_constraints(req.query)
        print(f"[Extractor] Results: {extracted_dict}")

        # Step 2: Merge logic
        # We prioritize user-provided JSON over AI-extracted guesses
        if req.constraints:
            explicit = req.constraints.model_dump(exclude_none=True)
            merged = {**extracted_dict, **explicit}
            print("[2/3] Merged explicit user constraints.")
        else:
            merged = extracted_dict
            print("[2/3] Using auto-extracted constraints.")

        constraints = Constraints(**merged)

        # Step 3: Generate architecture (This includes RAG + Ollama)
        print("[3/3] Generating architecture with RAG context...")
        result = await generate_architecture(req.query, constraints)
        
        duration = time.time() - start_time
        print(f"--- Request Completed in {duration:.2f}s ---\n")
        return result

    except Exception as e:
        print(f"!!! ERROR in /generate: {str(e)}")
        # If the LLM fails completely, don't just crash the frontend
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")