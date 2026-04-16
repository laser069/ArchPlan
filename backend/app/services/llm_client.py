import json
import os
import re
import asyncio
from typing import Tuple, Dict, Any
from dotenv import load_dotenv, find_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(find_dotenv())

# Configuration constants
OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_llm(provider: str, model: str):
    """Factory to initialize the LLM based on provider."""
    common_params = {"temperature": 0.1}
    
    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            model_kwargs={"response_mime_type": "application/json"},
            **common_params
        )
    elif provider == "groq":
        return ChatGroq(
            model_name=model,
            groq_api_key=os.getenv("GROQ_API_KEY"),
            model_kwargs={"response_format": {"type": "json_object"}},
            **common_params
        )
    elif provider == "openrouter":
        return ChatOpenAI(
            model=model,
            openai_api_key=os.getenv("OPENROUTER_API_KEY"),
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://localhost:3000",
                "X-Title": "ArchPlan"
            },
            **common_params
        )
    else: # Default to Ollama
        return ChatOllama(
            model=model,
            base_url=OLLAMA_URL,
            format="json",
            **common_params
        )

async def call_llm(provider: str, model: str, prompt: str) -> Tuple[Dict, Dict]:
    """Call LLM and return parsed JSON + token usage."""
    
    llm = get_llm(provider, model)
    prompt_template = ChatPromptTemplate.from_template("{input}")
    
    # Execution
    try:
        raw_msg = await (prompt_template | llm).ainvoke({"input": prompt})
        content = raw_msg.content
    except Exception as e:
        raise RuntimeError(f"LLM connection error ({provider}): {str(e)}")

    # Parsing Logic - Enhanced to handle nested objects or list wrappers
    parsed = _parse_json_robustly(content)
    
    # Metadata extraction
    usage = _extract_usage(provider, raw_msg)
    
    return parsed, usage

def _parse_json_robustly(content: Any) -> Dict:
    """Handles string cleaning, markdown stripping, and regex extraction."""
    if isinstance(content, dict):
        return content
    
    if not isinstance(content, str):
        raise ValueError(f"Unexpected LLM content type: {type(content)}")

    # 1. Strip Markdown
    cleaned = re.sub(r"```json\s*|```\s*", "", content.strip())
    
    # 2. Direct Parse
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # 3. Fallback: Find first '{' and last '}'
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
            except json.JSONDecodeError:
                raise ValueError("LLM returned malformed JSON.")
        else:
            raise ValueError("No JSON object found in LLM response.")

    # 4. Normalize list wrappers (some models return [{...}])
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
        
    if not isinstance(data, dict):
        raise ValueError("LLM did not return a JSON dictionary.")
        
    return data

def _extract_usage(provider: str, raw_msg) -> Dict:
    """Unified token usage extractor."""
    usage = {"input": 0, "output": 0, "total": 0}
    
    if provider == "gemini":
        meta = getattr(raw_msg, "usage_metadata", {}) or {}
        usage["input"] = meta.get("input_tokens", 0)
        usage["output"] = meta.get("output_tokens", 0)
    
    elif provider in ["groq", "openrouter"]:
        meta = getattr(raw_msg, "response_metadata", {}).get("token_usage", {})
        usage["input"] = meta.get("prompt_tokens", 0)
        usage["output"] = meta.get("completion_tokens", 0)

    else: # Ollama
        meta = getattr(raw_msg, "response_metadata", {})
        usage["input"] = meta.get("prompt_eval_count", 0)
        usage["output"] = meta.get("eval_count", 0)

    usage["total"] = usage["input"] + usage["output"]
    return usage