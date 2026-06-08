from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from beanie import Document
from pydantic import BaseModel, Field


class DiagramSnapshot(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    raw_nodes: List[List[str]] = Field(default_factory=list)
    raw_edges: List[List[str]] = Field(default_factory=list)
    components: List[Dict[str, Any]] = Field(default_factory=list)


class ChatMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["user", "assistant"]
    content: str
    diagram: Optional[DiagramSnapshot] = None
    scaling: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatSession(Document):
    user_email: str
    title: str = ""
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "chat_sessions"
        indexes = [
            [("user_email", 1), ("updated_at", -1)],
        ]


# ── Request / Response Pydantic models ──────────────────────────────────────

class SendMessageRequest(BaseModel):
    content: str
    provider: Literal["gemini", "ollama", "groq", "openrouter"] = "groq"
    model: Optional[str] = None


class RenameSessionRequest(BaseModel):
    title: str


class ChatSessionSummary(BaseModel):
    id: str
    title: str
    updated_at: datetime
    message_count: int


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime
