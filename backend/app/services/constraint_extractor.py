import json
import re
import httpx
import asyncio
from typing import Dict, Any

# Configuration
import os
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

# ============================================================
# CLASSIFIER SYSTEM PROMPT
# ============================================================
CLASSIFIER_PROMPT = """Extract constraints from user text. Return raw JSON only. Omit missing fields. Return {} if none.
Fields: budget_usd_month(int), team_size(int), peak_rps(int, daily_users/86400*10 round to 10), cloud_provider(AWS|GCP|Azure|DigitalOcean|Hetzner), region(str), stack([str]), avoid([str]), compliance([str]: GDPR/HIPAA/SOC2/PCI-DSS/ISO27001/CCPA only), scale_level(startup|growth|enterprise)
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
                clean[key] = list(set(v.upper() for v in flat_list if v.upper() in VALID_COMPLIANCE))
            else:
                clean[key] = list(set(flat_list))

    # 4. Region normalization
    if isinstance(data.get("region"), str):
        clean["region"] = data["region"].strip().lower()

    return clean

# ============================================================
# MAIN LOGIC
# ============================================================

def _keyword_fallback(query: str) -> Dict[str, Any]:
    q = query.lower()
    result: Dict[str, Any] = {}

    if any(w in q for w in ["million users", "millions of", "high traffic", "10k rps", "100k rps", "large scale", "enterprise", "global"]):
        result["scale_level"] = "enterprise"
    elif any(w in q for w in ["startup", "mvp", "minimum viable", "small team", "prototype", "side project"]):
        result["scale_level"] = "startup"
    elif any(w in q for w in ["growing", "scale up", "thousands of users", "medium"]):
        result["scale_level"] = "growth"

    if "aws" in q:
        result["cloud_provider"] = "AWS"
    elif "gcp" in q or "google cloud" in q:
        result["cloud_provider"] = "GCP"
    elif "azure" in q:
        result["cloud_provider"] = "Azure"
    elif "digitalocean" in q or "digital ocean" in q:
        result["cloud_provider"] = "DigitalOcean"

    compliance = []
    for tag, keywords in [
        ("HIPAA", ["hipaa", "healthcare", "medical", "patient data"]),
        ("GDPR", ["gdpr", "european", "eu users", "eu compliance"]),
        ("PCI-DSS", ["pci", "payment", "credit card", "stripe", "checkout"]),
        ("SOC2", ["soc2", "soc 2"]),
    ]:
        if any(k in q for k in keywords):
            compliance.append(tag)
    if compliance:
        result["compliance"] = compliance

    return result


async def extract_constraints(raw_query: str) -> Dict[str, Any]:
    """Calls Ollama to extract constraints. Falls back to keyword extraction on failure."""
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
        extracted = sanitize_extracted(data)

        # Merge keyword fallback for any fields Ollama left empty
        if not extracted:
            return _keyword_fallback(raw_query)
        fallback = _keyword_fallback(raw_query)
        for k, v in fallback.items():
            if k not in extracted:
                extracted[k] = v
        return extracted

    except Exception as e:
        print(f"[Extractor Error] {str(e)} — using keyword fallback")
        return _keyword_fallback(raw_query)