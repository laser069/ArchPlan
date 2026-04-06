from fastapi import APIRouter
from app.models.schema import GenerateRequest, GenerateResponse, Constraints
from app.services.llm_service import generate_architecture
from app.services.constraint_extractor import extract_constraints

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    # Step 1: extract constraints from the raw query string
    extracted_dict = await extract_constraints(req.query)

    # Step 2: if user also passed explicit constraints in JSON, merge them
    # (explicit JSON fields override extracted ones — user knows best)
    if req.constraints:
        explicit = req.constraints.model_dump(exclude_none=True)
        merged = {**extracted_dict, **explicit}
    else:
        merged = extracted_dict

    constraints = Constraints(**merged)

    # Step 3: generate architecture
    return await generate_architecture(req.query, constraints)