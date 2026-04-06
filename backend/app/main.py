from fastapi import FastAPI
from app.routes import generate

app = FastAPI(title="ArchPlan API")

app.include_router(generate.router)
