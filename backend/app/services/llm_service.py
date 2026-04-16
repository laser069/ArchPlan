import json
from typing import List
from app.models.schema import GenerateResponse, Constraints, Component
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt, get_refine_prompt
from app.services.llm_client import call_llm
from collections import Counter

# Configuration
HUB_TYPES = {"M", "C", "Q"}
HUB_FAN_THRESHOLD = 4 # Increased slightly to avoid over-collapsing

TYPE_MAP = {
    "S": "Service", "G": "Gateway", "Q": "Queue", "C": "Cache", "R": "Storage",
    "X": "CDN", "L": "LoadBalancer", "D": "Database", "A": "Auth", "M": "Monitor",
    "E": "Search", "W": "Worker", "N": "Network", "P": "Proxy"
}
REVERSE_TYPE_MAP = {v: k for k, v in TYPE_MAP.items()}

DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5-coder:7b-instruct-q4_0",
    "openrouter": "meta-llama/llama-3.3-70b-instruct"
}

def _extract_edges_from_diagram(diagram: str):
    """
    Surgical extraction of edges. 
    Crucial: It must handle subgraphs and notes without getting confused.
    """
    if not diagram: return []
    edges = []
    # Regex-like manual search for --> while ignoring 'note' lines
    for line in diagram.split("\n"):
        line = line.strip()
        if "-->" in line and "note[" not in line:
            # Handle potential Mermaid syntax: NodeA --> NodeB
            parts = line.split("-->")
            if len(parts) == 2:
                # Remove Mermaid brackets/IDs: API[Api Gateway] -> API
                a = parts[0].split("[")[0].strip().replace("_", " ")
                b = parts[1].split("[")[0].strip().replace("_", " ")
                edges.append([a, b])
    return edges

def _inflate(raw: dict) -> dict:
    """
    Converts raw LLM JSON into a rich UI response.
    Ensures 'n' and 'e' are preserved for future refinement loops.
    """
    nodes = raw.get("n", [])
    edges = raw.get("e", [])

    # Map raw nodes to Component objects
    components = [{"name": n, "type": TYPE_MAP.get(t, "Service")} for n, t in nodes]
    
    # Internal mapping for Mermaid IDs
    id_of = {n: n.replace(" ", "_") for n, _ in nodes}
    type_of = {n: t for n, t in nodes}

    tiers = {
        "Entry":         ["L", "G", "N", "X", "P"],
        "Logic":         ["S", "W", "A"],
        "Data":          ["D", "R", "C", "E", "Q"],
        "Observability": ["M"],
    }

    # --- Hub Collapsing Logic (For Visualization Only) ---
    in_degree = Counter(b for _, b in edges)
    hub_names = {
        n for n, t in nodes 
        if t in HUB_TYPES and in_degree.get(n, 0) > HUB_FAN_THRESHOLD
    }
    
    entry_chars = set(tiers["Entry"])
    
    # Generate the Mermaid String
    lines = ["graph TD"]
    for tier_name, types in tiers.items():
        tier_nodes = [n for n, t in nodes if t in types]
        if tier_nodes:
            lines.append(f"  subgraph {tier_name}")
            for node_name in tier_nodes:
                lines.append(f"    {id_of[node_name]}[{node_name}]")
            lines.append("  end")

    for a, b in edges:
        # If it's a hub, only show connections from Entry tier to keep it clean
        if b in hub_names and type_of.get(a) not in entry_chars:
            continue
        lines.append(f"  {id_of[a]} --> {id_of[b]}")

    if hub_names:
        lines.append(f"  note[\"Commonly used: {', '.join(hub_names)}\"]")

    return {
        "components": components,
        "diagram": "\n".join(lines),
        "architecture": raw.get("a", ""),
        "scaling": raw.get("s", ""),
        # CRITICAL: We pass the RAW nodes and edges back for the next Refinement call
        "raw_nodes": nodes, 
        "raw_edges": edges
    }

async def generate_architecture(
    query: str,
    provider: str = "groq",
    model: str = None,
    constraints: Constraints = None,
    existing_diagram: str = None,
    existing_components: List[dict] = None,
    cached_constraints: dict = None,
) -> GenerateResponse:
    
    # 1. Normalize Constraints
    constraints_to_use = constraints or Constraints()
    if cached_constraints:
        # Merge or prioritize cached constraints to prevent "forgetting" budget/rps
        constraints_to_use = Constraints(**{**cached_constraints, **constraints_to_use.model_dump(exclude_none=True)})
    
    c_str = json.dumps(constraints_to_use.model_dump(exclude_none=True))

    # 2. Build Prompt
    if existing_diagram and existing_components:
        # REFINEMENT MODE
        # Extract the node list in [[name, type_char]] format
        nodes_data = [
            [c["name"], REVERSE_TYPE_MAP.get(c["type"], "S")] 
            for c in existing_components
        ]
        # Get edges. We use the diagram as the source of truth for current wiring.
        edges_data = _extract_edges_from_diagram(existing_diagram)
        
        prompt = get_refine_prompt(
            query=query, 
            existing_nodes=json.dumps(nodes_data), 
            existing_edges=json.dumps(edges_data), 
            constraints_data=c_str
        )
    else:
        # NEW GENERATION MODE
        docs = get_relevant_docs(query, n_results=3)
        context_str = f" PATTERNS: {docs}" if docs else ""
        prompt = get_system_prompt(query, c_str + context_str)

    # 3. Provider Fallback Logic
    active_chain = ["groq", "openrouter", "gemini", "ollama"]
    if provider in active_chain:
        # Reorder to start with the user's choice
        active_chain.remove(provider)
        active_chain.insert(0, provider)

    for i, p_curr in enumerate(active_chain):
        try:
            target_model = model if (i == 0 and model) else DEFAULT_MODELS.get(p_curr)
            if not target_model: continue
            
            raw, usage = await call_llm(p_curr, target_model, prompt)
            
            # Inflate the data for the UI
            inflated = _inflate(raw)
            
            # Construct the final response
            resp = GenerateResponse(**inflated)
            resp.constraints = constraints_to_use.model_dump(exclude_none=True)
            return resp

        except Exception as e:
            print(f"[LLM ERROR] {p_curr} failed: {e}")
            continue

    # 4. Global Fallback if everything fails
    return GenerateResponse(
        components=[{"name": "App", "type": "Service"}],
        diagram="graph TD\n  App",
        architecture="All providers failed.",
        scaling="N/A"
    )