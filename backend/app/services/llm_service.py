import json
import requests
from app.models.schema import GenerateResponse

OLLAMA_URL = "http://localhost:11434/api/generate"

SYSTEM_PROMPT = """
You are a senior system design engineer.

Return ONLY valid JSON.

FORMAT:
{
  "components": [],
  "architecture": "",
  "scaling": "",
  "diagram": ""
}
"""

def extract_json(text: str):
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return text[start:end+1]
    return text


async def generate_architecture(query: str) -> GenerateResponse:
    prompt = f"{SYSTEM_PROMPT}\nUser: {query}"

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": "qwen2.5-coder:7b-instruct-q4_0",
            "prompt": prompt,
            "stream": False
        }
    )

    result = response.json()
    content = result.get("response", "").strip()

    try:
        clean = extract_json(content)
        data = json.loads(clean)
    except Exception:
        raise ValueError(f"Invalid JSON:\n{content}")

    return GenerateResponse(**data)