import json
import re
import httpx
from app.models.schema import GenerateResponse, Constraints
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt, get_refine_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

REQUIRED_KEYS = {"components", "architecture", "scaling", "diagram"}

def clean_and_parse(raw_text: str):
    try:
        text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
        text = re.sub(r"```json|```", "", text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            print(f"[Parse] no JSON object found in output")
            return None
        parsed = json.loads(match.group())
        return parsed
    except json.JSONDecodeError as e:
        print(f"[Parse] JSON decode failed: {e}")
        raw_snippet = raw_text[max(0, e.pos - 80) : e.pos + 80] if hasattr(e, 'pos') else raw_text[:200]
        print(f"[Parse]    Near: ...{raw_snippet}...")
        return None
    except Exception as e:
        print(f"[Parse] Unexpected error: {type(e).__name__}: {e}")
        return None

def sanitize_output(data: dict) -> dict:
    if "diagram" in data:
        data["diagram"] = data["diagram"].replace("\n", " ").replace("\r", " ").strip()

    valid_types = {
        "Service", "Gateway", "Queue", "Cache", "Storage", "CDN",
        "LoadBalancer", "Database", "Auth", "Monitor", "Search",
        "Worker", "Network", "Proxy"
    }
    normalized = []
    for comp in data.get("components", []):
        # Fix: model sometimes outputs "id" instead of "name"
        name = comp.get("name") or comp.get("id") or "Unknown"
        raw_type = comp.get("type", "Service")
        matched = next((t for t in valid_types if t.lower() in raw_type.lower()), "Service")
        normalized.append({"name": name, "type": matched})

    data["components"] = normalized

    # Fix: reject empty required string fields
    for key in ("architecture", "scaling", "diagram"):
        if key in data and not str(data[key]).strip():
            data.pop(key)

    return data

async def _call_ollama(client: httpx.AsyncClient, prompt: str, num_ctx: int = 6144, num_predict: int = 2048) -> str:
    response = await client.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": num_ctx,
                "num_predict": num_predict,   # hard cap — prevents mid-JSON cutoff
            }
        }
    )
    response.raise_for_status()
    raw = response.json()

    # Warn if model hit the token limit
    if raw.get("done_reason") == "length":
        print(f"[Ollama] ⚠️  Hit num_predict limit ({num_predict}) — output was truncated!")

    return raw.get("response", "")

def _validate_and_build(parsed_data: dict, attempt: int):
    sanitized = sanitize_output(parsed_data)
    missing = REQUIRED_KEYS - sanitized.keys()
    if missing:
        print(f"[Validate] Attempt {attempt + 1}: Missing keys {missing}")
        return None
    try:
        return GenerateResponse(**sanitized)
    except Exception as e:
        print(f"[Validate] Attempt {attempt + 1}: Build failed: {type(e).__name__}: {e}")
        return None

async def generate_architecture(
    query: str,
    constraints: Constraints = None,
    existing_diagram: str = None,
    existing_components: list = None,
    cached_constraints: dict = None,
) -> GenerateResponse:
    constraints = constraints or Constraints()
    is_refine = bool(existing_diagram)

    async with httpx.AsyncClient(timeout=300.0) as client:

        # FAST PATH: REFINEMENT
        if is_refine:
            constraints_str = json.dumps(
                cached_constraints or constraints.model_dump(exclude_none=True), indent=2
            )
            components_str = json.dumps(existing_components or [], indent=2)
            prompt = get_refine_prompt(query, existing_diagram, components_str, constraints_str)
            print(f"[LLM] FAST REFINE PATH")

            for attempt in range(2):
                try:
                    raw_json = await _call_ollama(client, prompt, num_ctx=3072, num_predict=1500)
                    print(f"[Refine] Attempt {attempt + 1} raw (first 400):\n{raw_json[:400]}\n")
                    parsed = clean_and_parse(raw_json)
                    if parsed:
                        result = _validate_and_build(parsed, attempt)
                        if result:
                            return result
                except Exception as e:
                    print(f"[Refine] Attempt {attempt + 1} exception: {type(e).__name__}: {e}")

            print("[Refine] Both attempts failed - fallback")
            return build_fallback(query)

        # STANDARD PATH: NEW DESIGN
        rag_docs = get_relevant_docs(query, n_results=3)
        constraints_str = json.dumps(constraints.model_dump(exclude_none=True), indent=2)
        if rag_docs:
            constraints_str += f"\n\nPRIORITY PATTERNS:\n{rag_docs}"

        prompt = get_system_prompt(query, constraints_str)
        print(f"[LLM] FULL GENERATE PATH")

        for attempt in range(2):
            try:
                raw_json = await _call_ollama(client, prompt, num_ctx=6144, num_predict=2048)
                print(f"[Generate] Attempt {attempt + 1} raw (first 400):\n{raw_json[:400]}\n")
                parsed = clean_and_parse(raw_json)
                if parsed:
                    result = _validate_and_build(parsed, attempt)
                    if result:
                        return result
            except Exception as e:
                print(f"[Generate] Attempt {attempt + 1} exception: {type(e).__name__}: {e}")

    print("[Generate] Both attempts failed - fallback")
    return build_fallback(query)

def build_fallback(query: str) -> GenerateResponse:
    return GenerateResponse(
        components=[
            {"name": "App Service", "type": "Service"},
            {"name": "Database", "type": "Database"}
        ],
        architecture=f"Standard design for {query}.",
        scaling="Vertical scaling for startup phase.",
        diagram="graph TD; App-->Database;"
    )