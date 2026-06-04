# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArchPlan is an AI-powered system architecture design assistant. Users describe system requirements in natural language; the app extracts constraints, retrieves relevant patterns from a RAG knowledge base, and generates interactive ReactFlow diagrams via a multi-provider LLM pipeline.

## Commands

### Backend
```bash
cd backend
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000       # dev server
python -m app.rag.ingest                        # rebuild vector DB from PDFs in backend/docs/
python -m pytest                                # run tests
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev       # http://localhost:3000
pnpm build
pnpm lint
```

### Prerequisites (must be running)
- MongoDB on default port
- Ollama with model `qwen2.5-coder:7b-instruct-q4_0`

API docs available at `http://localhost:8000/docs` when backend is running.

## Architecture

### Request Flow
1. Frontend sends `POST /generate` with `query`, `provider`, optional `existing_diagram`
2. `constraint_extractor.py` uses Ollama (temp=0) to parse constraints from the query
3. `retriever.py` queries ChromaDB for relevant architecture patterns
4. `llm_service.py` calls providers in order: Gemini → Groq → OpenRouter → Ollama fallback
5. Response contains ReactFlow `nodes`/`edges` + descriptive text; frontend renders via `Canvas.tsx`

### Key Backend Files
- `backend/app/services/llm_service.py` — orchestrates constraint extraction + LLM generation
- `backend/app/services/prompts.py` — all system prompts (initial generation vs. refinement)
- `backend/app/services/constraint_extractor.py` — deterministic Ollama-based extraction
- `backend/app/services/llm_client.py` — multi-provider abstraction (Gemini, Groq, OpenRouter, Ollama)
- `backend/app/rag/retriever.py` — ChromaDB similarity search
- `backend/app/rag/ingest.py` — PDF ingestion (chunk size 1200, overlap 300)
- `backend/app/models/schema.py` — Pydantic v2 request/response models
- `backend/app/models/database.py` — Beanie Document models (MongoDB: `users`, `generation_history`)
- `backend/app/routes/auth.py` — JWT login/signup endpoints
- `backend/app/routes/generate.py` — main generation endpoint with auth guard

### Key Frontend Files
- `frontend/app/page.tsx` — main UI (query input, diagram display)
- `frontend/components/Canvas.tsx` — ReactFlow renderer with Dagre layout
- `frontend/hooks/useArchitecture.ts` — API call hook

### Component Type System
Node types are lowercase descriptive strings — infra terms (`gateway`, `service`, `loadbalancer`, `auth`, `cache`, `queue`, `database`, `monitor`, `cdn`, `search`, `worker`, `proxy`, `storage`) or specific tech (`redis`, `postgresql`, `kafka`, `nginx`, `elasticsearch`). `_get_tier()` in `llm_service.py` maps type strings to layout tiers: Entry → Logic → Data/Observability. Every generated architecture must include ≥1 each of: load balancer, auth, cache, monitor.

### Graph Constraints
- No orphan nodes — every node must have ≥1 edge
- Data flow must be traceable: ingress → ... → storage
- Auth node must sit on the hot path
- Monitor node must have in-edges from major service/data nodes

### Authentication
JWT (HS256, 60-min expiry), bcrypt_sha256 passwords. Frontend stores token in `localStorage` and sends `Authorization: Bearer {token}` on all API calls. Protected routes use `get_current_user()` FastAPI dependency.

## Important Notes

- **Pydantic v2**: All models use `ConfigDict`. Do not use deprecated v1 syntax (`class Config`, `orm_mode`, `schema_extra`).
- **Frontend Next.js version**: Read `node_modules/next/dist/docs/` before writing frontend code — this version has breaking changes from training data (see `frontend/CLAUDE.md`).
- **`existing_diagram`** must be passed as a dict (not string) for refinement flows.
- **LLM temperature**: constraint extraction uses temp=0 (deterministic); generation uses temp=0.1.
- Backend environment variables live in `backend/.env`: `GOOGLE_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `OLLAMA_BASE_URL`, `SECRET_KEY`.

## Git Workflow

### Branch Strategy

Before starting any implementation, create or switch to a feature branch:

```bash
git checkout -b <type>/<scope>   # new branch
git checkout <existing-branch>   # or switch to existing
```

Branch naming mirrors commit type/scope conventions:
- `fix/auth-secret-key`
- `fix/frontend-security`
- `feat/canvas-edges`
- `refactor/llm-types`

**Rules:**
- Never commit directly to `main`
- One branch per logical change — don't bundle unrelated fixes
- Branch name must match the type of work being done

### Commit Message Format
```
<type>(<scope>): <short description>
```
- **type**: `feat` | `fix` | `docs` | `refactor` | `chore` | `test`
- **scope**: optional, one word (e.g. `auth`, `rag`, `canvas`)
- **description**: imperative, lowercase, ≤50 chars, no trailing period

**Examples:**
```
feat(auth): add JWT refresh token endpoint
fix(rag): handle empty ChromaDB query result
docs: update backend setup instructions
chore: bump pydantic to 2.7
```

**Rules:**
- Subject line ≤ 72 characters total
- No vague messages (`update stuff`, `fix bug`, `changes`)
- One logical change per commit — do not bundle unrelated fixes
