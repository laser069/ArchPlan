from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.routes import generate
from app.models.database import ArchHistory # Import the new model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB connection
    # Replace with your actual URI if using Atlas
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=client.ArchPlanDB, 
        document_models=[ArchHistory]
    )
    print("--- MongoDB Initialized ---")
    yield
    client.close()

app = FastAPI(title="ArchPlan API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)