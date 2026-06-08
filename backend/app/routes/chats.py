from __future__ import annotations
import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth import get_current_user
from app.models.chat import (
    ChatMessage,
    ChatSession,
    ChatSessionResponse,
    ChatSessionSummary,
    DiagramSnapshot,
    RenameSessionRequest,
    SendMessageRequest,
)
from app.models.schema import Component, Constraints, GenerateResponse, User
from app.core.validators import validate_constraints, validate_generate_request
from app.core.cache import get_cached_constraints, cache_constraint_extraction
from app.services.constraint_extractor import extract_constraints
from app.services.llm_service import generate_architecture
from app.services.prompts import get_refine_prompt, get_system_prompt
from app.models.database import ArchHistory

router = APIRouter(prefix="/chats", tags=["Chats"])
logger = logging.getLogger(__name__)


def _session_to_response(session: ChatSession) -> ChatSessionResponse:
    return ChatSessionResponse(
        id=str(session.id),
        title=session.title,
        messages=session.messages,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


async def _log_to_training_db(
    query: str,
    provider: str,
    model: Optional[str],
    result: GenerateResponse,
    is_refine: bool,
    user_email: str,
) -> None:
    try:
        if is_refine:
            nodes_data = [[c.name, c.type] for c in result.components]
            prompt = get_refine_prompt(
                query=query,
                existing_nodes=json.dumps(nodes_data),
                existing_edges=json.dumps(result.raw_edges),
                constraints_data=json.dumps(result.constraints),
            )
        else:
            prompt = get_system_prompt(
                query, json.dumps(result.constraints), context="[rag_context_not_stored]"
            )

        db_entry = ArchHistory(
            user_email=user_email,
            query=query,
            full_prompt=prompt,
            provider=provider,
            model_name=model or "DEFAULT",
            architecture_narrative=result.architecture,
            nodes=result.nodes,
            edges=result.edges,
            raw_nodes=result.raw_nodes,
            raw_edges=result.raw_edges,
            scaling=result.scaling,
            components=[{"name": c.name, "type": c.type} for c in result.components],
            constraints=result.constraints,
            is_gold_standard=False,
        )
        await db_entry.insert()
    except Exception:
        logger.exception("_log_to_training_db failed")


# ── GET /chats ────────────────────────────────────────────────────────────────

@router.get("", response_model=list[ChatSessionSummary])
async def list_sessions(current_user: User = Depends(get_current_user)):
    sessions = (
        await ChatSession.find(ChatSession.user_email == current_user.email)
        .sort("-updated_at")
        .limit(100)
        .to_list()
    )
    return [
        ChatSessionSummary(
            id=str(s.id),
            title=s.title or "Untitled",
            updated_at=s.updated_at,
            message_count=len(s.messages),
        )
        for s in sessions
    ]


# ── POST /chats ───────────────────────────────────────────────────────────────

@router.post("", response_model=ChatSessionResponse, status_code=201)
async def create_session(current_user: User = Depends(get_current_user)):
    session = ChatSession(
        user_email=current_user.email,
        title="",
    )
    await session.insert()
    return _session_to_response(session)


# ── GET /chats/{id} ───────────────────────────────────────────────────────────

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = await ChatSession.get(PydanticObjectId(session_id))
    if not session or session.user_email != current_user.email:
        raise HTTPException(status_code=404, detail="Chat not found")
    return _session_to_response(session)


# ── PATCH /chats/{id} ─────────────────────────────────────────────────────────

@router.patch("/{session_id}", response_model=ChatSessionResponse)
async def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    current_user: User = Depends(get_current_user),
):
    session = await ChatSession.get(PydanticObjectId(session_id))
    if not session or session.user_email != current_user.email:
        raise HTTPException(status_code=404, detail="Chat not found")
    session.title = body.title.strip()[:80]
    session.updated_at = datetime.now(timezone.utc)
    await session.save()
    return _session_to_response(session)


# ── DELETE /chats/{id} ────────────────────────────────────────────────────────

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    session = await ChatSession.get(PydanticObjectId(session_id))
    if not session or session.user_email != current_user.email:
        raise HTTPException(status_code=404, detail="Chat not found")
    await session.delete()
    return {"ok": True}


# ── POST /chats/{id}/messages ─────────────────────────────────────────────────

@router.post("/{session_id}/messages", response_model=ChatSessionResponse)
async def send_message(
    session_id: str,
    body: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    session = await ChatSession.get(PydanticObjectId(session_id))
    if not session or session.user_email != current_user.email:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Detect refine: last assistant message has a diagram
    last_assistant = next(
        (m for m in reversed(session.messages) if m.role == "assistant" and m.diagram),
        None,
    )
    is_refine = last_assistant is not None

    existing_diagram = None
    existing_components = None
    if is_refine:
        d = last_assistant.diagram
        existing_diagram = {"nodes": d.nodes, "edges": d.edges}
        existing_components = d.components

    # Build constraints
    try:
        if is_refine:
            # For refinement, reuse cached constraints from last assistant message
            cached_data = last_assistant.constraints or {}
            constraints = Constraints(**cached_data)
        else:
            cached = get_cached_constraints(body.content)
            if cached:
                extracted = cached
            else:
                extracted = await extract_constraints(body.content)
                cache_constraint_extraction(body.content, extracted)
            constraints = Constraints(**extracted)

        is_valid, error_msg = validate_constraints(constraints)
        if not is_valid:
            raise HTTPException(status_code=422, detail=error_msg)

        # Generate
        result = await generate_architecture(
            query=body.content,
            provider=body.provider,
            model=body.model,
            constraints=constraints,
            existing_diagram=existing_diagram,
            existing_components=existing_components,
        )
        result = result.model_copy(
            update={"constraints": constraints.model_dump(exclude_none=True)}
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    # Append user message
    user_msg = ChatMessage(role="user", content=body.content)
    session.messages.append(user_msg)

    # Append assistant message
    assistant_msg = ChatMessage(
        role="assistant",
        content=result.architecture,
        diagram=DiagramSnapshot(
            nodes=result.nodes,
            edges=result.edges,
            raw_nodes=result.raw_nodes,
            raw_edges=result.raw_edges,
            components=[{"name": c.name, "type": c.type} for c in result.components],
        ),
        scaling=result.scaling,
        constraints=result.constraints,
        provider=body.provider,
        model_name=body.model or "DEFAULT",
    )
    session.messages.append(assistant_msg)

    # Auto-title from first user message
    if not session.title:
        session.title = body.content[:60].strip()

    session.updated_at = datetime.now(timezone.utc)
    await session.save()

    background_tasks.add_task(
        _log_to_training_db,
        body.content,
        body.provider,
        body.model,
        result,
        is_refine,
        current_user.email,
    )

    return _session_to_response(session)
