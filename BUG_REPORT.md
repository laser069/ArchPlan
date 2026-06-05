# ArchPlan Bug Audit Report

**Date:** 2026-06-04  
**Branch:** `fix/security-and-bugs`  
**Auditor:** Claude Sonnet 4.6 (code-debugger agent)

---

## 1. Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 4 |
| 🟠 HIGH | 7 |
| 🟡 MEDIUM | 6 |
| 🟢 LOW | 5 |
| **Total** | **22** |

---

## 2. Bug Table

| File | Line(s) | Severity | Description |
|------|---------|----------|-------------|
| `backend/app/routes/auth.py` | 10 | 🔴 CRITICAL | Signup credentials sent as query params, not body |
| `backend/app/main.py` | 27–32 | 🔴 CRITICAL | CORS wildcard + `allow_credentials=True` — spec violation |
| `frontend/app/page.tsx` | 73 | 🔴 CRITICAL | `mark-gold` POSTs to a backend route that does not exist |
| `backend/app/services/constraint_extractor.py` | 8 | 🔴 CRITICAL | `OLLAMA_URL` hardcoded, ignores `OLLAMA_BASE_URL` env var |
| `backend/app/routes/generate.py` | 110–113 | 🟠 HIGH | `HTTPException` re-wrapped as 500, destroys real status code |
| `backend/app/routes/generate.py` | 124 | 🟠 HIGH | History sorted by `"-id"` instead of `"-created_at"` |
| `backend/app/routes/generate.py` | 65 | 🟠 HIGH | `is_refine` set from `existing_diagram` alone; diverges from service logic |
| `backend/app/models/database.py` | 28 | 🟠 HIGH | `created_at` uses `datetime.now()` (naive/local) instead of UTC |
| `backend/app/core/cache.py` | 40, 57, 137 | 🟠 HIGH | All cache timestamps use `datetime.now()` (naive) |
| `backend/app/services/llm_client.py` | 59 | 🟠 HIGH | `max_tokens=512` too small for complex diagram generation |
| `backend/app/core/validators.py` | 20–57 | 🟠 HIGH | `validate_generate_request` defined but never called |
| `frontend/hooks/useArchitecture.ts` | 44–46 | 🟡 MEDIUM | 401 swallowed silently — no redirect, no user feedback |
| `backend/app/services/llm_service.py` | 93 | 🟡 MEDIUM | Edge type lookup fragile — space vs underscore mismatch |
| `backend/app/services/llm_service.py` | 128 | 🟡 MEDIUM | `cached_constraints` merge order inverts precedence on refinement |
| `frontend/app/signup/page.tsx` | 21–25 | 🟡 MEDIUM | Frontend sends JSON body; backend reads query params → always 422 |
| `backend/app/core/logging_config.py` | 19 | 🟡 MEDIUM | `datetime.utcnow()` deprecated in Python 3.12+ |
| `backend/app/services/constraint_extractor.py` | 71 | 🟡 MEDIUM | Compliance filter O(n×m) redundant `.upper()` calls |
| `frontend/app/page.tsx` | 37–42 | 🟢 LOW | JWT decoded client-side via `atob` — no signature verification |
| `backend/app/models/schema.py` | 23 | 🟢 LOW | `cloud_provider` default `"AWS"` silently overrides unrecognised values |
| `frontend/components/Canvas.tsx` | 207 | 🟢 LOW | `setTimeout(..., 50)` for `fitView` — race condition on slow renders |
| `backend/app/routes/generate.py` | 101–102 | 🟢 LOW | Constraints not attached to refinement response — frontend cache stale |
| `backend/app/core/validators.py` | 86–97 | 🟢 LOW | `sanitize_query` defined but never called |

---

## 3. 🔴 CRITICAL Bugs

---

### C-1 — Signup credentials exposed in URL query parameters

**File:** `backend/app/routes/auth.py:10`  
**Category:** Security

The `/signup` endpoint receives `email` and `password` as query string parameters. Query params appear in every reverse proxy log, web server access log, and browser history. Passwords are exposed in plaintext.

The frontend (`signup/page.tsx:21–25`) sends a JSON body with `Content-Type: application/json`, which FastAPI ignores for primitive query parameters — the body is silently discarded. FastAPI requires `?email=...&password=...` in the URL. The frontend never sends that, so every signup call returns **422 Unprocessable Entity**. Signup is completely broken.

```python
# Current — WRONG
@auth_router.post("/signup")
async def signup(email: str, password: str):  # reads from query string
```

**Fix:** Define a Pydantic `SignupRequest` body model and use it as the parameter type:
```python
class SignupRequest(BaseModel):
    email: str
    password: str

@auth_router.post("/signup")
async def signup(req: SignupRequest):
```

---

### C-2 — CORS wildcard + `allow_credentials=True` — spec violation

**File:** `backend/app/main.py:27–32`  
**Category:** Security

The CORS spec and all conforming browsers prohibit `allow_origins=["*"]` combined with `allow_credentials=True`. Browsers will refuse credentialed cross-origin requests when the response echoes a wildcard `Access-Control-Allow-Origin`. Any request from the frontend that includes credentials (cookies, auth headers) will be blocked.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ← wildcard
    allow_credentials=True,   # ← combined with wildcard: spec violation
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Fix:** Replace wildcard with an explicit allowlist:
```python
allow_origins=["http://localhost:3000", os.getenv("FRONTEND_URL", "")],
```

---

### C-3 — `mark-gold` calls a route that does not exist

**File:** `frontend/app/page.tsx:73`  
**Category:** Runtime

`toggleGoldStandard` POSTs to `http://localhost:8000/history/mark-gold`. No such route is registered in the backend. Every invocation returns **404**, the error is caught, `isStarred` is set back to false. The "Mark Gold Standard" feature is completely non-functional and silently fails.

```typescript
const res = await fetch('http://localhost:8000/history/mark-gold', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
```

**Fix:** Implement `POST /history/mark-gold` on the backend, or remove the dead button.

---

### C-4 — `constraint_extractor.py` hardcodes Ollama URL, ignores env var

**File:** `backend/app/services/constraint_extractor.py:8`  
**Category:** Runtime / Configuration

`OLLAMA_URL` is hardcoded as `"http://localhost:11434/api/generate"`, completely ignoring the `OLLAMA_BASE_URL` environment variable that `llm_client.py` correctly reads. In any non-localhost deployment, constraint extraction silently fails on every request, returning `{}` for all constraints. The extractor's `except` block swallows the connection error — failure is invisible.

```python
# constraint_extractor.py line 8 — hardcoded
OLLAMA_URL = "http://localhost:11434/api/generate"

# llm_client.py line 16 — correct pattern
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
```

**Fix:**
```python
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate"
```

---

## 4. 🟠 HIGH Bugs

---

### H-1 — `HTTPException` re-wrapped as 500

**File:** `backend/app/routes/generate.py:110–113`  
**Category:** Logic

The outer `except Exception` in `generate_endpoint` catches `HTTPException` (which inherits from `Exception`) and re-raises it as a new `HTTPException(status_code=500)`. A 401 from `get_current_user`, a 422 from `validate_constraints`, or a 503 from the LLM service all arrive at the client as 500. The `useArchitecture` hook's `response.status === 401` session-expiry check is permanently broken because of this.

```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # swallows 401, 422, 503
```

**Fix:**
```python
except HTTPException:
    raise
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

---

### H-2 — History sorted by `"-id"` instead of `"-created_at"`

**File:** `backend/app/routes/generate.py:124`  
**Category:** Logic

`.sort("-id")` sorts by a Python attribute named `id`, not the MongoDB `_id`. The model defines a `created_at` field explicitly for chronological ordering which is ignored.

**Fix:** `.sort("-created_at")`

---

### H-3 — `is_refine` diverges from service logic

**File:** `backend/app/routes/generate.py:65`  
**Category:** Logic

`is_refine = bool(req.existing_diagram)` but the service's refine branch requires **both** `existing_diagram` and `existing_components`. Sending one without the other causes the route to take the refine path for constraint handling while the service falls through to new-generation mode, producing a mismatched prompt saved to the database.

---

### H-4 — `created_at` uses naive `datetime.now()` (local time)

**File:** `backend/app/models/database.py:28`  
**Category:** Logic

`default_factory=datetime.now` stores the server's local wall-clock time with no timezone. MongoDB stores datetimes as UTC BSON — a naive local datetime is misinterpreted. History sort order breaks across DST transitions.

**Fix:** `default_factory=lambda: datetime.now(timezone.utc)`

---

### H-5 — Cache timestamps naive — timezone inconsistency

**File:** `backend/app/core/cache.py:40,57,137`  
**Category:** Logic

All TTL comparisons use `datetime.now()` (naive local time). Entries can expire immediately or never expire across DST boundaries or timezone changes. Cache functions are also never called from any route or service — dead code at runtime, latent bug if wired in.

**Fix:** Replace all `datetime.now()` with `datetime.now(timezone.utc)`

---

### H-6 — `max_tokens=512` too small for diagram generation

**File:** `backend/app/services/llm_client.py:59`  
**Category:** Performance / Logic

The default `max_tokens=512` is too small for architecture JSON with many nodes and edges. Truncated output causes `_parse_json_robustly` to raise `ValueError`, which triggers the fallback chain — meaning every provider is tried and fails before returning 503. Complex queries silently degrade to empty responses.

**Fix:** Pass `max_tokens=2048` (or `4096`) in the `call_llm` invocation inside `generate_architecture`.

---

### H-7 — `validate_generate_request` never called

**File:** `backend/app/core/validators.py:20–57`  
**Category:** Logic (dead validation)

`validate_generate_request` validates query length, provider values, component counts, and edge counts. It is imported nowhere and called nowhere. A client can send an empty query, 10,000 components, or 50,000 edges — all reach the LLM unchecked.

**Fix:** Add at the top of `generate_endpoint`:
```python
is_valid, msg = validate_generate_request(req)
if not is_valid:
    raise HTTPException(status_code=422, detail=msg)
```

---

## 5. 🟡 MEDIUM Bugs

---

### M-1 — 401 swallowed silently, no user redirect

**File:** `frontend/hooks/useArchitecture.ts:44–46`  
**Category:** Logic

When the backend returns 401, the hook logs to console and returns. No redirect to `/login`, no error state set. User sees the spinner disappear with no message. Note: also permanently broken by H-1 — all errors arrive as 500, so this branch never executes.

```typescript
if (response.status === 401) {
  console.error("Session expired. Please log in again.");
  // Optional: window.location.href = '/login';  ← never activated
  return;
}
```

---

### M-2 — Edge type lookup uses display names but IDs use underscores

**File:** `backend/app/services/llm_service.py:93`  
**Category:** Logic

`type_of = {n: t for n, t in nodes}` maps display names (`"Core API"`) to types. Edge animation is looked up via `type_of.get(target)` where `target` comes from the edge list. Node ID generation at line 70 replaces spaces with `_`, creating a key mismatch. Any space/case difference returns `None`, making `is_animated` always `False` for most edges.

---

### M-3 — `cached_constraints` merge inverts precedence on refinement

**File:** `backend/app/services/llm_service.py:128`  
**Category:** Logic

During refinement, `constraints_to_use` is built from `cached_constraints`, then `cached_constraints` is passed again to the service which merges cached on top. If the user changes a constraint during refinement, the cached value wins and the update is silently dropped.

---

### M-4 — Signup frontend/backend parameter mismatch (runtime consequence of C-1)

**File:** `frontend/app/signup/page.tsx:21–25` + `backend/app/routes/auth.py:10`  
**Category:** Runtime

Frontend sends JSON body; backend reads query params. FastAPI returns 422 for every signup attempt. Both sides need to be fixed together (see C-1).

---

### M-5 — `datetime.utcnow()` deprecated in Python 3.12+

**File:** `backend/app/core/logging_config.py:19`  
**Category:** Runtime

`datetime.utcnow()` is deprecated since Python 3.12 and removed in 3.14+. Returns naive datetime with no tzinfo.

**Fix:** `datetime.now(timezone.utc).isoformat()`

---

### M-6 — Compliance filter O(n×m) redundant `.upper()` calls

**File:** `backend/app/services/constraint_extractor.py:71`  
**Category:** Performance

```python
[c.upper() for c in VALID_COMPLIANCE]  # VALID_COMPLIANCE is already uppercase
```

`VALID_COMPLIANCE` is already a set of uppercase strings. The inner comprehension recreates it on every outer loop iteration.

**Fix:** `if v.upper() in VALID_COMPLIANCE`

---

## 6. 🟢 LOW Bugs

---

### L-1 — Client-side JWT decode via `atob` — no signature verification

**File:** `frontend/app/page.tsx:37–42`  
**Category:** Security (UI-only, low impact)

`atob` decodes the base64 payload without verifying the JWT signature. Any valid base64-encoded JSON with a `sub` field bypasses the UI guard. Backend enforces real auth, so this is not exploitable for data access — but a crafted token suppresses the redirect-to-login, showing the (non-functional) UI to logged-out users.

---

### L-2 — `cloud_provider` default `"AWS"` silently overrides unrecognised values

**File:** `backend/app/models/schema.py:23`  
**Category:** Logic

`cloud_provider: str = "AWS"` has no `Literal` constraint. An LLM or client sending `cloud_provider: "azure"` (lowercase) is accepted by Pydantic but then dropped by `sanitize_extracted` (which checks exact-case). The model silently defaults to `"AWS"`. Users who specify Azure get AWS constraints with no indication.

**Fix:** `Optional[Literal["AWS","GCP","Azure","DigitalOcean","Hetzner"]] = None`

---

### L-3 — `fitView` via `setTimeout(50ms)` — race condition on slow renders

**File:** `frontend/components/Canvas.tsx:207`  
**Category:** Performance / Logic

```typescript
setTimeout(() => fitView({ padding: 0.2, duration: 600 }), 50);
```

50ms is an arbitrary magic number. On slow devices or with many nodes, the layout may not be committed within 50ms, causing `fitView` to calculate bounds against an incomplete layout.

**Fix:** Use `requestAnimationFrame` after `setNodes`/`setEdges`.

---

### L-4 — Constraints not attached to refinement response — frontend cache stale

**File:** `backend/app/routes/generate.py:101–102`  
**Category:** Logic

Constraints are only written to the response on initial generation, not on refinement. If a user changes a constraint during refinement, the updated constraints are not returned — the frontend caches the stale old values and sends them on the next refinement iteration.

---

### L-5 — `sanitize_query` defined but never called

**File:** `backend/app/core/validators.py:86–97`  
**Category:** Logic (dead code)

`sanitize_query` strips extra whitespace and enforces `MAX_QUERY_LENGTH`. Never imported or called. Raw user input — including malformed whitespace and oversized strings — goes directly into the LLM prompt.

---

## 7. Additional Configuration Gap

**File:** `backend/app/main.py:15`

```python
AsyncIOMotorClient("mongodb://localhost:27017")  # hardcoded
```

Same pattern as C-4. In any deployed environment this fails. Should read from `MONGODB_URI` env var. Not promoted to CRITICAL since it only affects deployed environments, not local dev.

---

## 8. Fix Priority

| Priority | Bugs | Reason |
|----------|------|--------|
| Fix immediately | C-1, C-2, C-3, C-4, H-1 | Broken core features + security |
| Fix before release | H-2 to H-7, M-1, M-4 | Correctness + silent failures |
| Fix soon | M-2, M-3, M-5, M-6, L-4, L-5 | Quality + future-proofing |
| Nice to have | L-1, L-2, L-3 | Polish |
