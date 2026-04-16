import json
import re
import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5-coder:7b-instruct-q4_0"

# ============================================================
#  CLASSIFIER SYSTEM PROMPT
# ============================================================
CLASSIFIER_PROMPT = """You are a constraint extraction engine for a system design tool.

Your ONLY job is to read the user's raw text and extract any technical constraints they mentioned.
Return a single raw JSON object. No markdown. No backticks. No explanation. Start with { end with }.

════════════════════════
FIELDS YOU CAN EXTRACT
════════════════════════
- "budget_usd_month"  → integer. Extract any monthly budget in USD.
                         "$1500/mo" → 1500 | "two thousand dollar budget" → 2000 | "₹50,000" → 600 (convert to USD approx)
- "team_size"         → integer. Number of engineers/developers.
                         "3 devs" → 3 | "small team of 5" → 5 | "solo" → 1
- "peak_rps"          → integer. Requests per second at peak load.
                         "10k users/day" → 12 | "1M req/day" → 12 | "500 RPS" → 500 | "100k concurrent" → 1000
- "cloud_provider"    → string. One of: "AWS", "GCP", "Azure", "DigitalOcean", "Hetzner".
                         "Google Cloud" → "GCP" | "Amazon" → "AWS" | "Microsoft Azure" → "Azure"
- "region"            → string. AWS/GCP/Azure region code.
                         "India" → "ap-south-1" | "US East" → "us-east-1" | "Europe" → "eu-west-1"
                         "Singapore" → "ap-southeast-1" | "Mumbai" → "ap-south-1" | "Frankfurt" → "eu-central-1"
                         "US West" → "us-west-2" | "Tokyo" → "ap-northeast-1" | "Sydney" → "ap-southeast-2"
- "stack"             → list of strings. Programming languages, frameworks, databases explicitly preferred.
                         "Python backend" → ["Python"] | "use Postgres and React" → ["PostgreSQL", "React"]
                         "Node.js" → ["Node.js"] | "Django" → ["Python", "Django"]
- "avoid"             → list of strings. Technologies explicitly rejected or too expensive.
                         "no Kubernetes" → ["Kubernetes"] | "avoid Kafka, too expensive" → ["Kafka"]
                         "don't use microservices" → ["Microservices"] | "no managed services" → ["Managed Services"]
- "compliance"        → list of strings. Regulatory or compliance requirements.
                         "GDPR compliant" → ["GDPR"] | "healthcare app" → ["HIPAA"]
                         "payment processing" → ["PCI-DSS"] | "government" → ["SOC2"]
- "scale_level"       → string. One of: "startup", "growth", "enterprise".
                         "MVP" → "startup" | "early stage" → "startup" | "scaling up" → "growth"
                         "enterprise" → "enterprise" | "100M users" → "enterprise" | "Series A" → "growth"

════════════════════════
RULES
════════════════════════
- If a field is NOT mentioned, DO NOT include it in the output.
- If the user gives a raw system name like "Design Netflix" with NO constraints → return {}
- Never guess or hallucinate constraints. Only extract what is explicitly or strongly implied.
- "healthcare app" strongly implies HIPAA. "payment app" strongly implies PCI-DSS. These are valid inferences.
- Convert load estimates: daily users ÷ 86400 × peak_factor(10) = approx RPS
- Output ONLY the JSON. Nothing else.

════════════════════════
FEW-SHOT EXAMPLES
════════════════════════

Input: "Design Netflix"
Output: {}

Input: "I have a $2000/month AWS budget, team of 4 devs, no Kubernetes please, prefer Python and PostgreSQL"
Output: {"budget_usd_month":2000,"cloud_provider":"AWS","team_size":4,"avoid":["Kubernetes"],"stack":["Python","PostgreSQL"]}

Input: "Build a food delivery app for India, startup scale, 3 engineers, GDPR compliant, avoid Kafka and Kubernetes, Python backend, expect 10k orders per day"
Output: {"region":"ap-south-1","scale_level":"startup","team_size":3,"compliance":["GDPR"],"avoid":["Kafka","Kubernetes"],"stack":["Python"],"peak_rps":12}

Input: "Healthcare patient portal, enterprise scale, HIPAA required, Java stack, AWS us-east-1, 500 RPS peak, team of 20"
Output: {"compliance":["HIPAA"],"scale_level":"enterprise","stack":["Java"],"cloud_provider":"AWS","region":"us-east-1","peak_rps":500,"team_size":20}

Input: "Solo founder, MVP, $500/month max, no managed services, just a simple app"
Output: {"team_size":1,"budget_usd_month":500,"scale_level":"startup","avoid":["Managed Services"]}

Input: "E-commerce platform, Google Cloud, Singapore region, expect 1 million users per day, Series B startup"
Output: {"cloud_provider":"GCP","region":"ap-southeast-1","peak_rps":120,"scale_level":"growth"}

Input: "Payment gateway system, PCI-DSS must, Azure, European users, 200 RPS, mid-size team of 12"
Output: {"compliance":["PCI-DSS"],"cloud_provider":"Azure","region":"eu-west-1","peak_rps":200,"team_size":12}

Input: "Messaging app like WhatsApp, massive scale, 500M users, enterprise, avoid anything expensive"
Output: {"scale_level":"enterprise","peak_rps":5000,"avoid":["Expensive Managed Services"]}

════════════════════════
FINAL REMINDER
════════════════════════
Output ONLY raw JSON. Start with {. End with }. No other text.
If nothing can be extracted, return {}
"""


# ============================================================
#  HELPERS (same as llm_service.py — keep in sync)
# ============================================================

def clean_output(text: str) -> str:
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def extract_json_str(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    raise ValueError("No JSON found")


async def call_model(prompt: str) -> str:
    """Call Ollama model with better error handling and retries."""
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:  # Reduced timeout
                response = await client.post(
                    OLLAMA_URL,
                    json={
                        "model": MODEL_NAME,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.0,   # zero temp — extraction must be deterministic
                            "num_predict": 300,   # constraints JSON is always short
                            "top_p": 1.0,
                        }
                    }
                )
                response.raise_for_status()  # Raise exception for HTTP errors
                return response.json().get("response", "").strip()
        except httpx.TimeoutException:
            if attempt < max_retries:
                print(f"[Extractor] Timeout, retrying ({attempt + 1}/{max_retries})...")
                await asyncio.sleep(1)  # Brief pause before retry
                continue
            print("[Extractor] Timeout after retries, falling back to empty constraints")
            return "{}"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 500:
                if attempt < max_retries:
                    print(f"[Extractor] Server error, retrying ({attempt + 1}/{max_retries})...")
                    await asyncio.sleep(2)  # Longer pause for server errors
                    continue
                print("[Extractor] Server error after retries, falling back to empty constraints")
                return "{}"
            else:
                print(f"[Extractor] HTTP error {e.response.status_code}, falling back to empty constraints")
                return "{}"
        except Exception as e:
            print(f"[Extractor] Unexpected error: {e}, falling back to empty constraints")
            return "{}"


# ============================================================
#  SANITIZERS  — clean up common model mistakes
# ============================================================

VALID_CLOUD_PROVIDERS = {"AWS", "GCP", "Azure", "DigitalOcean", "Hetzner"}
VALID_SCALE_LEVELS = {"startup", "growth", "enterprise"}
VALID_COMPLIANCE = {"GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001", "CCPA"}

def sanitize_extracted(data: dict) -> dict:
    clean = {}

    # budget
    if "budget_usd_month" in data:
        try:
            clean["budget_usd_month"] = max(0, int(data["budget_usd_month"]))
        except (ValueError, TypeError):
            pass

    # team_size
    if "team_size" in data:
        try:
            clean["team_size"] = max(1, int(data["team_size"]))
        except (ValueError, TypeError):
            pass

    # peak_rps
    if "peak_rps" in data:
        try:
            clean["peak_rps"] = max(1, int(data["peak_rps"]))
        except (ValueError, TypeError):
            pass

    # cloud_provider
    if "cloud_provider" in data:
        val = str(data["cloud_provider"]).strip()
        if val in VALID_CLOUD_PROVIDERS:
            clean["cloud_provider"] = val

    # region (just pass through — too many valid values to enumerate)
    if "region" in data and isinstance(data["region"], str):
        clean["region"] = data["region"].strip()

    # stack — must be list of strings
    if "stack" in data and isinstance(data["stack"], list):
        clean["stack"] = [str(s).strip() for s in data["stack"] if s]

    # avoid — must be list of strings
    if "avoid" in data and isinstance(data["avoid"], list):
        clean["avoid"] = [str(s).strip() for s in data["avoid"] if s]

    # compliance — normalize to uppercase known values
    if "compliance" in data and isinstance(data["compliance"], list):
        normalized = []
        for c in data["compliance"]:
            upper = str(c).strip().upper()
            # match loosely
            matched = next((v for v in VALID_COMPLIANCE if v.upper() == upper), str(c).strip())
            normalized.append(matched)
        clean["compliance"] = normalized

    # scale_level
    if "scale_level" in data:
        val = str(data["scale_level"]).strip().lower()
        if val in VALID_SCALE_LEVELS:
            clean["scale_level"] = val

    return clean


# ============================================================
#  MAIN EXPORT
# ============================================================

async def extract_constraints(raw_query: str) -> dict:
    """
    Takes a raw freeform user query string.
    Returns a clean dict of extracted constraints (may be empty).
    Never raises — on any failure returns {}.
    """
    prompt = f"{CLASSIFIER_PROMPT}\n\nInput: {raw_query}\nOutput:"

    print(f"\n[Extractor] Classifying: '{raw_query[:80]}...'")

    try:
        raw_output = await call_model(prompt)
        if not raw_output or raw_output.strip() == "":
            print("[Extractor] Empty response from model, using no constraints")
            return {}

        print(f"[Extractor] Raw output: {raw_output[:200]}")

        cleaned = clean_output(raw_output)
        if not cleaned:
            print("[Extractor] No content after cleaning, using no constraints")
            return {}

        try:
            json_str = extract_json_str(cleaned)
            data = json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[Extractor] JSON parsing failed: {e}, using no constraints")
            return {}

        result = sanitize_extracted(data)
        print(f"[Extractor] Extracted: {result}")
        return result

    except Exception as e:
        print(f"[Extractor] Unexpected error: {e}, using no constraints")
        return {}