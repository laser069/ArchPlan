import json
import os
import re
from dotenv import load_dotenv, find_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(find_dotenv())

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

async def call_llm(provider: str, model: str, prompt: str) -> tuple[dict, dict]:
    """Call LLM (Gemini or Ollama) and return parsed JSON + token usage."""
    llm = (
        ChatGoogleGenerativeAI(
            model=model,
            google_api_key=GEMINI_KEY,
            temperature=0.1,
            model_kwargs={"response_mime_type": "application/json"}
        ) if provider == "gemini" else
        ChatOllama(model=model, base_url=OLLAMA_URL, temperature=0.1, format="json")
    )

    prompt_template = ChatPromptTemplate.from_template("{input}")
    raw_msg = await (prompt_template | llm).ainvoke({"input": prompt})

    content = raw_msg.content
    if isinstance(content, str):
        cleaned_content = re.sub(r"^```json\s*|^```\s*|```\s*$", "", content.strip(), flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON decode failed: {e}")
            try:
                parsed = JsonOutputParser().parse(cleaned_content)
            except Exception as parse_error:
                print(f"[DEBUG] JsonOutputParser failed: {parse_error}")
                raise ValueError(f"Failed to parse LLM output: {cleaned_content[:200]}")
    elif isinstance(content, (dict, list)):
        parsed = content
    else:
        parsed = content

    if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict):
        parsed = parsed[0]

    if not isinstance(parsed, dict):
        raise ValueError(f"LLM output must be a JSON object, got {type(parsed).__name__}")

    usage = _extract_usage(provider, raw_msg)
    return parsed, usage

def _extract_usage(provider: str, raw_msg) -> dict:
    """Extract token counts from LLM response message object."""
    if provider == "gemini":
        u = getattr(raw_msg, "usage_metadata", None) or {}
        return {
            "input":  u.get("input_tokens", 0),
            "output": u.get("output_tokens", 0),
            "total":  u.get("total_tokens", 0),
        }
    meta = raw_msg.response_metadata or {}
    inp = meta.get("prompt_eval_count", 0) or meta.get("inputs", 0) or 0
    out = meta.get("eval_count", 0) or meta.get("outputs", 0) or 0
    return {"input": inp, "output": out, "total": inp + out}