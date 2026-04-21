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
    nodes = raw.get("n", [])
    edges = raw.get("e", [])
    type_of = {n: t for n, t in nodes}

    # Configuration for layout math
    LAYER_WIDTH = 900
    LAYER_HEIGHT = 200
    LAYER_GAP = 50  # Space between layers
    NODE_X_STEP = 220 # Horizontal space between nodes in a layer
    
    tiers = {
        "Entry":         ["L", "G", "N", "X", "P"],
        "Logic":         ["S", "W", "A"],
        "Data":          ["D", "R", "C", "E", "Q"],
        "Observability": ["M"],
    }

    formatted_nodes = []
    formatted_edges = []

    # 1. Create Tier "Group" Nodes with Y-offsets
    current_y = 0
    for tier_name in tiers.keys():
        formatted_nodes.append({
            "id": tier_name,
            "type": "group",
            "data": {"label": f"{tier_name} Layer"},
            "position": {"x": 0, "y": current_y},
            # CRITICAL: Parent groups need explicit dimensions
            "style": {
                "width": LAYER_WIDTH, 
                "height": LAYER_HEIGHT,
                "backgroundColor": "rgba(6, 182, 212, 0.02)",
                "border": "1px solid rgba(6, 182, 212, 0.1)",
                "borderRadius": "8px"
            }
        })
        current_y += (LAYER_HEIGHT + LAYER_GAP)

    # 2. Map Components to Nodes with horizontal spreading
    tier_counts = {k: 0 for k in tiers.keys()} # Track how many nodes in each tier

    for node_name, type_char in nodes:
        node_id = node_name.replace(" ", "_")
        parent_tier = "Logic" 
        for t_name, t_chars in tiers.items():
            if type_char in t_chars:
                parent_tier = t_name
                break
        
        # Calculate relative position inside the parent
        x_pos = 40 + (tier_counts[parent_tier] * NODE_X_STEP)
        tier_counts[parent_tier] += 1
        
        formatted_nodes.append({
            "id": node_id,
            "parentId": parent_tier,
            "type": "architectureNode", # Matches your custom component
            "data": {
                "label": node_name,
                "type": TYPE_MAP.get(type_char, "Service")
            },
            # Position is relative to the top-left of the 'parent_tier' group
            "position": {"x": x_pos, "y": 60}, 
            "extent": "parent"
        })

    # 3. Map Connections to Edges
    for i, (source, target) in enumerate(edges):
        s_id = source.replace(" ", "_")
        t_id = target.replace(" ", "_")
        
        # Determine if we should animate (Queues and Caches usually imply flow)
        is_animated = type_of.get(target) in ["Q", "C"]
        
        formatted_edges.append({
            "id": f"e{i}-{s_id}-{t_id}",
            "source": s_id,
            "target": t_id,
            "animated": is_animated,
            "style": {"stroke": "#06b6d4", "strokeWidth": 2}
        })

    return {
        "components": [{"name": n, "type": TYPE_MAP.get(t, "Service")} for n, t in nodes],
        "nodes": formatted_nodes,
        "edges": formatted_edges,
        "architecture": raw.get("a", ""),
        "scaling": raw.get("s", ""),
        "raw_nodes": nodes, 
        "raw_edges": edges
    }
async def generate_architecture(
    query: str,
    provider: str = "groq",
    model: str = None,
    constraints: Constraints = None,
    existing_diagram: dict = None,
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
        # Get edges from the diagram dict's edges list
        edges_data = existing_diagram.get("edges", []) if isinstance(existing_diagram, dict) else []
        
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
    fallback_data = {
        "n": [["App", "S"]],
        "e": [],
        "a": "All providers failed. Please try again.",
        "s": "N/A"
    }
    fallback_inflated = _inflate(fallback_data)
    return GenerateResponse(**fallback_inflated)