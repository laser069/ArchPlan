import json
from typing import List
from app.models.schema import GenerateResponse, Constraints, Component
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt, get_refine_prompt
from app.services.llm_client import call_llm

TYPE_MAP = {
    "S": "Service", "G": "Gateway", "Q": "Queue", "C": "Cache", "R": "Storage",
    "X": "CDN", "L": "LoadBalancer", "D": "Database", "A": "Auth", "M": "Monitor",
    "E": "Search", "W": "Worker", "N": "Network", "P": "Proxy"
}
REVERSE_TYPE_MAP = {v: k for k, v in TYPE_MAP.items()}

# Updated MODELS to include Groq
MODELS = {
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5-coder:7b-instruct-q4_0",
}

def _extract_edges_from_diagram(diagram: str):
    """Extract edge pairs from Mermaid graph TD format."""
    if not diagram or "graph TD" not in diagram:
        return []
    edges = []
    # Normalizing potential whitespace/newline differences
    cleaned_diagram = diagram.replace("graph TD;", "").replace("graph TD", "")
    for part in cleaned_diagram.split(";"):
        part = part.strip()
        if "-->" in part:
            a, b = part.split("-->", 1)
            edges.append([a.strip().replace("_", " "), b.strip().replace("_", " ")])
    return edges

def _inflate(raw: dict) -> dict:
    """Convert compact raw output into the frontend schema."""
    nodes = raw.get("n", [])
    edges = raw.get("e", [])

    components = [
        {"name": n, "type": TYPE_MAP.get(t, "Service")}
        for n, t in nodes
    ]

    id_of = {n: n.replace(" ", "_") for n, _ in nodes}
    edge_strs = "; ".join(f'{id_of.get(a, a)}-->{id_of.get(b, b)}' for a, b in edges)
    diagram = f"graph TD; {edge_strs}"

    return {
        "components": components,
        "diagram": diagram,
        "architecture": raw.get("a", ""),
        "scaling": raw.get("s", ""),
    }

async def generate_architecture(
    query: str,
    provider: str = "groq",  # Defaulting to Groq for speed and 70B reasoning
    constraints: Constraints = None,
    existing_diagram: str = None,
    existing_components: List[dict] = None,
    cached_constraints: dict = None,
) -> GenerateResponse:
    constraints = constraints or Constraints()
    c_str = json.dumps(constraints.model_dump(exclude_none=True))

    if existing_diagram:
        nodes_str = json.dumps([
            [c["name"], REVERSE_TYPE_MAP.get(c["type"], "S")]
            for c in (existing_components or [])
        ])
        edges_str = json.dumps(_extract_edges_from_diagram(existing_diagram))
        prompt = get_refine_prompt(query, nodes_str, edges_str, c_str)
    else:
        docs = get_relevant_docs(query, n_results=3)
        if docs:
            c_str += f" PATTERNS:{docs}"
        prompt = get_system_prompt(query, c_str)

    # Retry/Fallback Logic: Groq -> Gemini -> Ollama
    # This ensures if you hit Groq's rate limit, you fall back to other free options
    provider_chain = ["groq", "gemini", "ollama"]
    
    # Start the chain from the user's requested provider
    if provider in provider_chain:
        current_index = provider_chain.index(provider)
        active_chain = provider_chain[current_index:]
    else:
        active_chain = [provider] + provider_chain

    for provider_curr in active_chain:
        try:
            model = MODELS.get(provider_curr)
            if not model: continue
            
            print(f"[LLM] {provider_curr}/{model} attempting...")

            raw, usage = await call_llm(provider_curr, model, prompt)
            print(f"[tokens] {provider_curr} in={usage['input']} out={usage['output']}")

            return GenerateResponse(**_inflate(raw))
            
        except Exception as e:
            print(f"[LLM] Error with {provider_curr}: {e}")
            # Continue to next provider in the chain
            continue

    # Final Fallback if all providers fail
    return GenerateResponse(
        components=[
            Component(name="App", type="Service"),
            Component(name="DB", type="Database")
        ],
        architecture="All LLM providers are currently unavailable.",
        scaling="N/A",
        diagram="graph TD; App-->DB;"
    )