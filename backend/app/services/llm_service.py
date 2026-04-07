import json
import re
import httpx
from app.models.schema import GenerateResponse, Constraints
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

# --- HELPERS ---

def clean_and_parse(raw_text: str) -> dict:
    """Extracts JSON from LLM noise and parses it."""
    try:
        text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found")
        return json.loads(match.group())
    except Exception as e:
        print(f"Parse Error: {e}")
        return None

def sanitize_output(data: dict) -> dict:
    """Ensures diagram is single-line and types are valid."""
    if "diagram" in data:
        data["diagram"] = data["diagram"].replace("\n", " ").replace("\r", " ").strip()
    
    valid_types = {"Service", "Gateway", "Queue", "Cache", "Storage", "CDN", "LoadBalancer", "Database", "Auth", "Monitor", "Search", "Worker", "Network", "Proxy"}
    
    normalized = []
    for comp in data.get("components", []):
        name = comp.get("name", "Unknown")
        raw_type = comp.get("type", "Service")
        matched = next((t for t in valid_types if t.lower() in raw_type.lower()), "Service")
        normalized.append({"name": name, "type": matched})
    
    data["components"] = normalized
    return data

# --- CORE LOGIC ---

async def generate_architecture(query: str, constraints: Constraints = None, existing_diagram: str = None) -> GenerateResponse:
    constraints = constraints or Constraints()
    
    # 1. Context Gathering (RAG)
    rag_docs = get_relevant_docs(query, n_results=3)
    constraints_str = json.dumps(constraints.model_dump(exclude_none=True), indent=2)
    if rag_docs:
        constraints_str += f"\n\nPRIORITY PATTERNS:\n{rag_docs}"

    # 2. Build Dynamic Prompt
    prompt = get_system_prompt(query, constraints_str, existing_diagram)

    # 3. Execution Loop
    async with httpx.AsyncClient(timeout=300.0) as client:
        for attempt in range(2):
            try:
                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.1, "num_ctx": 4096}
                    }
                )
                response.raise_for_status()
                raw_json = response.json().get("response", "")
                
                parsed_data = clean_and_parse(raw_json)
                if parsed_data:
                    final_data = sanitize_output(parsed_data)
                    return GenerateResponse(**final_data)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                continue

    # 4. Fallback if AI fails
    return build_fallback(query)

def build_fallback(query: str) -> GenerateResponse:
    return GenerateResponse(
        components=[{"name": "App Service", "type": "Service"}, {"name": "Database", "type": "Database"}],
        architecture=f"Standard design for {query}.",
        scaling="Vertical scaling for startup phase.",
        diagram="graph TD; App-->Database;"
    )