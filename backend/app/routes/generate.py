from fastapi import APIRouter
from app.models.schema import GenerateRequest, GenerateResponse
from app.services.llm_service import generate_architecture

router = APIRouter()

@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    result = await generate_architecture(req.query)
    return result
