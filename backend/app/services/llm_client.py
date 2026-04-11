import json
import os
import re
from dotenv import load_dotenv, find_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI  # Added for OpenRouter
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(find_dotenv())

GEMINI_KEY = os.getenv("GOOGLE_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

async def call_llm(provider: str, model: str, prompt: str) -> tuple[dict, dict]:
    """Call LLM (Gemini, Ollama, Groq, or OpenRouter) and return parsed JSON + token usage."""
    
    if provider == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=GEMINI_KEY,
            temperature=0.1,
            model_kwargs={"response_mime_type": "application/json"}
        )
    elif provider == "groq":
        llm = ChatGroq(
            model_name=model,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}}
        )
    elif provider == "openrouter":
        # OpenRouter uses the OpenAI-compatible class
        llm = ChatOpenAI(
            model=model,
            openai_api_key=OPENROUTER_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
            model_kwargs={"response_format": {"type": "json_object"}},
            # OpenRouter specific headers (optional but recommended)
            default_headers={
                "HTTP-Referer": "https://localhost:3000", 
                "X-Title": "ArchPlan"
            }
        )
    else:
        llm = ChatOllama(
            model=model, 
            base_url=OLLAMA_URL, 
            temperature=0.1, 
            format="json"
        )

    prompt_template = ChatPromptTemplate.from_template("{input}")
    raw_msg = await (prompt_template | llm).ainvoke({"input": prompt})

    # Parsing Logic
    content = raw_msg.content
    if isinstance(content, str):
        cleaned_content = re.sub(r"^```json\s*|^```\s*|```\s*$", "", content.strip(), flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(cleaned_content)
        except json.JSONDecodeError:
            try:
                parsed = JsonOutputParser().parse(cleaned_content)
            except Exception:
                raise ValueError(f"Failed to parse LLM output: {cleaned_content[:200]}")
    else:
        parsed = content

    if isinstance(parsed, list) and len(parsed) == 1 and isinstance(parsed[0], dict):
        parsed = parsed[0]

    if not isinstance(parsed, dict):
        raise ValueError(f"LLM output must be a JSON object, got {type(parsed).__name__}")

    usage = _extract_usage(provider, raw_msg)
    return parsed, usage

def _extract_usage(provider: str, raw_msg) -> dict:
    if provider == "gemini":
        u = getattr(raw_msg, "usage_metadata", None) or {}
        return {
            "input": u.get("input_tokens", 0),
            "output": u.get("output_tokens", 0),
            "total": u.get("total_tokens", 0),
        }
    
    if provider == "groq":
        u = raw_msg.response_metadata.get("token_usage", {})
        return {
            "input": u.get("prompt_tokens", 0),
            "output": u.get("completion_tokens", 0),
            "total": u.get("total_tokens", 0),
        }

    if provider == "openrouter":
        u = getattr(raw_msg, "response_metadata", {}).get("token_usage", {})
        return {
            "input": u.get("prompt_tokens", 0),
            "output": u.get("completion_tokens", 0),
            "total": u.get("total_tokens", 0),
        }

    # Ollama / Default
    meta = raw_msg.response_metadata or {}
    inp = meta.get("prompt_eval_count", 0) or meta.get("inputs", 0) or 0
    out = meta.get("eval_count", 0) or meta.get("outputs", 0) or 0
    return {"input": inp, "output": out, "total": inp + out}