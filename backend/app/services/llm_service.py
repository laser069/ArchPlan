import json
from typing import List
from app.models.schema import GenerateResponse, Constraints, Component
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt, get_refine_prompt
from app.services.llm_client import call_llm
from collections import Counter

HUB_TYPES = {"M", "C", "Q"}
HUB_FAN_THRESHOLD = 3

TYPE_MAP = {
    "S": "Service", "G": "Gateway", "Q": "Queue", "C": "Cache", "R": "Storage",
    "X": "CDN", "L": "LoadBalancer", "D": "Database", "A": "Auth", "M": "Monitor",
    "E": "Search", "W": "Worker", "N": "Network", "P": "Proxy"
}
REVERSE_TYPE_MAP = {v: k for k, v in TYPE_MAP.items()}

# Updated MODELS to include Groq
DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5-coder:7b-instruct-q4_0",
    "openrouter": "meta-llama/llama-3.3-70b-instruct"
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
    nodes = raw.get("n", [])
    edges = raw.get("e", [])

    components = [{"name": n, "type": TYPE_MAP.get(t, "Service")} for n, t in nodes]
    id_of = {n: n.replace(" ", "_") for n, _ in nodes}
    type_of = {n: t for n, t in nodes}

    tiers = {
        "Entry":         ["L", "G", "N", "X", "P"],
        "Logic":         ["S", "W", "A"],
        "Data":          ["D", "R", "C", "E", "Q"],
        "Observability": ["M"],
    }
    # Reverse lookup: type_char → tier name
    char_to_tier = {c: tier for tier, chars in tiers.items() for c in chars}

    # --- Hub collapsing ---
    # Count how many distinct sources feed into each node
    in_degree = Counter(b for _, b in edges if b in id_of)

    # Nodes that qualify as hubs: correct type + heavily connected
    hub_names = {
        n for n, t in nodes
        if t in HUB_TYPES and in_degree.get(n, 0) > HUB_FAN_THRESHOLD
    }

    # Entry-tier type chars — only these are allowed to connect to a hub
    entry_chars = set(tiers["Entry"])

    filtered_edges = []
    for a, b in edges:
        if a not in id_of or b not in id_of:
            continue
        if b in hub_names:
            # Keep edge only if source is an Entry-tier node (Gateway, LB, etc.)
            if type_of.get(a, "") in entry_chars:
                filtered_edges.append([a, b])
            # All other fan-out edges to this hub are dropped
        else:
            filtered_edges.append([a, b])

    # --- Mermaid build ---
    lines = ["graph TD"]

    for tier_name, types in tiers.items():
        tier_nodes = [n for n, t in nodes if t in types]
        if tier_nodes:
            lines.append(f"  subgraph {tier_name}")
            for node_name in tier_nodes:
                lines.append(f"    {id_of[node_name]}[{node_name}]")
            lines.append("  end")

    for a, b in filtered_edges:
        lines.append(f"  {id_of[a]} --> {id_of[b]}")

    # Annotate collapsed hubs so no information is silently lost
    if hub_names:
        hub_label = " | ".join(sorted(hub_names))
        lines.append(f"  note[\"Shared by all services: {hub_label}\"]")

    return {
        "components": components,
        "diagram": "\n".join(lines),
        "architecture": raw.get("a", ""),
        "scaling": raw.get("s", ""),
    }


async def generate_architecture(
    query: str,
    provider: str = "groq",
    model: str = None,  # Dynamic model name from frontend
    constraints: Constraints = None,
    existing_diagram: str = None,
    existing_components: List[dict] = None,
    cached_constraints: dict = None,
) -> GenerateResponse:
    constraints = constraints or Constraints()
    c_str = json.dumps(constraints.model_dump(exclude_none=True))

    # 1. Build Prompt (Refine vs New)
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

    # 2. Define the Provider Chain (Fallback Order)
    provider_chain = ["groq", "openrouter", "gemini", "ollama"]
    
    if provider in provider_chain:
        current_index = provider_chain.index(provider)
        active_chain = provider_chain[current_index:]
    else:
        active_chain = [provider] + provider_chain

    # 3. Execution Loop with Fallback
    for i, provider_curr in enumerate(active_chain):
        try:
            # LOGIC: Use 'model' only for the first attempt in the chain.
            # If the first attempt fails, fall back to the DEFAULT_MODELS for safety.
            target_model = model if (i == 0 and model) else DEFAULT_MODELS.get(provider_curr)
            
            if not target_model:
                continue
            
            print(f"[LLM] {provider_curr}/{target_model} attempting...")

            raw, usage = await call_llm(provider_curr, target_model, prompt)
            print(f"[tokens] {provider_curr} in={usage['input']} out={usage['output']}")

            # Construct response and inject the constraints for caching
            result = GenerateResponse(**_inflate(raw))
            if not existing_diagram:
                 result.constraints = constraints.model_dump(exclude_none=True)
            
            return result
            
        except Exception as e:
            print(f"[LLM] Error with {provider_curr}: {e}")
            # Continue to next provider in the chain using their default models
            continue

    # 4. Final Fallback
    return GenerateResponse(
        components=[
            Component(name="App", type="Service"),
            Component(name="DB", type="Database")
        ],
        architecture="All LLM providers are currently unavailable or the specific model requested failed.",
        scaling="N/A",
        diagram="graph TD; App-->DB;"
    )



