import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.routes import generate, auth, chats
from app.models.database import ArchHistory
from app.models.schema import User
from app.models.chat import ChatSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    await init_beanie(
        database=client.ArchPlanDB,
        document_models=[ArchHistory, User, ChatSession]
    )
    print("--- MongoDB Initialized ---")
    yield
    client.close()

app = FastAPI(title="ArchPlan API", lifespan=lifespan)

_origins = [o for o in ["http://localhost:3000", os.getenv("FRONTEND_URL", "")] if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(auth.auth_router)
app.include_router(chats.router)