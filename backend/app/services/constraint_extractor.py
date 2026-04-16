import json
import re
import httpx
import asyncio
from typing import Dict, Any

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

# ============================================================
# CLASSIFIER SYSTEM PROMPT
# ============================================================
CLASSIFIER_PROMPT = """You are a constraint extraction engine. 
Identify technical constraints from the user's text. Return ONLY a single raw JSON object. 

FIELDS:
- "budget_usd_month": integer.
- "team_size": integer.
- "peak_rps": integer. (Formula: daily users / 86400 * 10. Round to nearest 10).
- "cloud_provider": "AWS", "GCP", "Azure", "DigitalOcean", or "Hetzner".
- "region": string (e.g., "us-east-1", "ap-south-1").
- "stack": list of strings (e.g., ["Python", "PostgreSQL"]).
- "avoid": list of strings (e.g., ["Kubernetes"]).
- "compliance": list of strings (e.g., ["GDPR", "HIPAA"]).
- "scale_level": "startup", "growth", or "enterprise".

RULES:
- If a field is not mentioned, OMIT it. 
- If no constraints found, return {}.
- Output ONLY JSON. No explanation or markdown.
"""

# ============================================================
# VALIDATION SETS
# ============================================================
VALID_CLOUD_PROVIDERS = {"AWS", "GCP", "Azure", "DigitalOcean", "Hetzner"}
VALID_SCALE_LEVELS = {"startup", "growth", "enterprise"}
VALID_COMPLIANCE = {"GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001", "CCPA"}

# ============================================================
# HELPERS
# ============================================================

def _extract_json_strictly(text: str) -> str:
    """Finds the first balanced JSON object in a string."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        return match.group(1)
    return "{}"

def sanitize_extracted(data: Dict[str, Any]) -> Dict[str, Any]:
    """Cleans and validates LLM output against allowed types/values."""
    clean = {}

    # 1. Numeric conversions (handles "120" or "120.0")
    for key in ["budget_usd_month", "team_size", "peak_rps"]:
        if key in data:
            try:
                val = int(float(data[key]))
                clean[key] = max(0 if key != "team_size" else 1, val)
            except (ValueError, TypeError):
                continue

    # 2. Categorical enforcements
    if data.get("cloud_provider") in VALID_CLOUD_PROVIDERS:
        clean["cloud_provider"] = data["cloud_provider"]

    if data.get("scale_level") in VALID_SCALE_LEVELS:
        clean["scale_level"] = data["scale_level"]

    # 3. List normalizations (Fixed to prevent "unhashable type: list" errors)
    for key in ["stack", "avoid", "compliance"]:
        val = data.get(key)
        if isinstance(val, list):
            flat_list = []
            for item in val:
                if isinstance(item, list):
                    # Unpack nested lists if LLM makes a mistake
                    flat_list.extend([str(i).strip() for i in item if i])
                elif item:
                    flat_list.append(str(item).strip())
            
            # Deduplicate safely now that all elements are strings
            if key == "compliance":
                clean[key] = list(set(v.upper() for v in flat_list if v.upper() in [c.upper() for c in VALID_COMPLIANCE]))
            else:
                clean[key] = list(set(flat_list))

    # 4. Region normalization
    if isinstance(data.get("region"), str):
        clean["region"] = data["region"].strip().lower()

    return clean

# ============================================================
# MAIN LOGIC
# ============================================================

async def extract_constraints(raw_query: str) -> Dict[str, Any]:
    """
    Calls Ollama to extract constraints. 
    Returns {} on failure to ensure the main flow is never blocked.
    """
    full_prompt = CLASSIFIER_PROMPT + "\nInput: " + raw_query + "\nOutput:"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 256,
                    }
                }
            )
            response.raise_for_status()
            raw_text = response.json().get("response", "")

        json_str = _extract_json_strictly(raw_text)
        data = json.loads(json_str)
        
        return sanitize_extracted(data)

    except Exception as e:
        # Log the error but return empty dict to keep the user moving
        print(f"[Extractor Error] {str(e)}")
        return {}