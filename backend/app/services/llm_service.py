import json
import re
from typing import List
from app.models.schema import GenerateResponse, Constraints, Component
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt, get_refine_prompt
from app.services.llm_client import call_llm

DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash",
    "groq": "llama-3.3-70b-versatile",
    "ollama": "qwen2.5-coder:7b-instruct-q4_0",
    "openrouter": "meta-llama/llama-3.3-70b-instruct"
}

def _get_tier(type_str: str) -> str:
    """Map a descriptive type string to a layout tier."""
    t = type_str.lower()
    if re.search(r'load.?balancer|lb|cdn|gateway|proxy|network|firewall|nginx|kong', t):
        return "Entry"
    if re.search(r'monitor|metric|log|prometheus|grafana|datadog|trace|alert', t):
        return "Observability"
    if re.search(
        r'database|db|postgres|mysql|mongo|dynamo|cassandra|sqlite|'
        r'cache|redis|memcache|queue|kafka|rabbit|sqs|sns|pubsub|'
        r'search|elastic|solr|algolia|storage|s3|blob|gcs|file', t
    ):
        return "Data"
    return "Logic"  # service, auth, worker, api, etc.


def _inflate(raw: dict) -> dict:
    nodes = raw.get("n", [])
    edges = raw.get("e", [])
    type_of = {n: t for n, t in nodes}

    LAYER_WIDTH = 900
    LAYER_HEIGHT = 200
    LAYER_GAP = 50
    NODE_X_STEP = 220

    tiers = ["Entry", "Logic", "Data", "Observability"]

    formatted_nodes = []
    formatted_edges = []

    # 1. Create tier group nodes
    current_y = 0
    for tier_name in tiers:
        formatted_nodes.append({
            "id": tier_name,
            "type": "group",
            "data": {"label": f"{tier_name} Layer"},
            "position": {"x": 0, "y": current_y},
            "style": {
                "width": LAYER_WIDTH,
                "height": LAYER_HEIGHT,
                "backgroundColor": "rgba(6, 182, 212, 0.02)",
                "border": "1px solid rgba(6, 182, 212, 0.1)",
                "borderRadius": "8px"
            }
        })
        current_y += (LAYER_HEIGHT + LAYER_GAP)

    # 2. Map components to nodes
    tier_counts = {t: 0 for t in tiers}

    for node_name, type_str in nodes:
        node_id = node_name.replace(" ", "_")
        parent_tier = _get_tier(type_str)

        x_pos = 40 + (tier_counts[parent_tier] * NODE_X_STEP)
        tier_counts[parent_tier] += 1

        formatted_nodes.append({
            "id": node_id,
            "parentId": parent_tier,
            "type": "architectureNode",
            "data": {
                "label": node_name,
                "type": type_str,
            },
            "position": {"x": x_pos, "y": 60},
            "extent": "parent"
        })

    # 3. Map edges
    for i, (source, target) in enumerate(edges):
        s_id = source.replace(" ", "_")
        t_id = target.replace(" ", "_")

        target_type = (type_of.get(target) or "").lower()
        is_animated = bool(re.search(r'queue|kafka|rabbit|sqs|cache|redis|pubsub', target_type))

        formatted_edges.append({
            "id": f"e{i}-{s_id}-{t_id}",
            "source": s_id,
            "target": t_id,
            "animated": is_animated,
            "style": {"stroke": "#06b6d4", "strokeWidth": 2}
        })

    return {
        "components": [{"name": n, "type": t} for n, t in nodes],
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

    # 1. Normalize constraints
    constraints_to_use = constraints or Constraints()
    if cached_constraints:
        constraints_to_use = Constraints(**{**cached_constraints, **constraints_to_use.model_dump(exclude_none=True)})

    c_str = json.dumps(constraints_to_use.model_dump(exclude_none=True))

    # 2. Build prompt
    if existing_diagram and existing_components:
        # REFINEMENT MODE — strip full ReactFlow edge objects to [src, tgt] pairs only
        nodes_data = [[c["name"], c["type"]] for c in existing_components]

        raw_edges = existing_diagram.get("edges", []) if isinstance(existing_diagram, dict) else []
        edges_data = [
            [e.get("source", "").replace("_", " "), e.get("target", "").replace("_", " ")]
            for e in raw_edges
            if isinstance(e, dict) and "source" in e and "target" in e
        ]

        prompt = get_refine_prompt(
            query=query,
            existing_nodes=json.dumps(nodes_data),
            existing_edges=json.dumps(edges_data),
            constraints_data=c_str
        )
    else:
        # NEW GENERATION MODE — RAG context in its own PATTERNS section
        docs = get_relevant_docs(query)
        prompt = get_system_prompt(query, c_str, context=docs)

    # 3. Provider fallback chain
    active_chain = ["groq", "openrouter", "gemini", "ollama"]
    if provider in active_chain:
        active_chain.remove(provider)
        active_chain.insert(0, provider)

    for i, p_curr in enumerate(active_chain):
        try:
            target_model = model if (i == 0 and model) else DEFAULT_MODELS.get(p_curr)
            if not target_model:
                continue

            raw, usage = await call_llm(p_curr, target_model, prompt)
            inflated = _inflate(raw)
            resp = GenerateResponse(**inflated)
            resp.constraints = constraints_to_use.model_dump(exclude_none=True)
            return resp

        except Exception as e:
            print(f"[LLM ERROR] {p_curr} failed: {e}")
            continue

    # 4. Global fallback
    fallback_data = {
        "n": [["App", "service"]],
        "e": [],
        "a": "All providers failed. Please try again.",
        "s": "N/A"
    }
    fallback_inflated = _inflate(fallback_data)
    return GenerateResponse(**fallback_inflated)
