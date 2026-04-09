import json
from typing import Dict, Any
import os
from dotenv import load_dotenv,find_dotenv

load_dotenv(find_dotenv())


# LangChain 2026 Core & Providers
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# Project Imports
from app.models.schema import GenerateResponse, Constraints
from app.rag.retriever import get_relevant_docs
from app.services.prompts import get_system_prompt, get_refine_prompt

# --- CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
OLLAMA_BASE_URL = "http://localhost:11434"
REQUIRED_KEYS = {"components", "architecture", "scaling", "diagram"}

# --- LLM CLIENT HELPERS (The "llmclient" Logic) ---

def _get_llm_instance(provider: str, model_name: str):
    """
    Acts as the 'Client Factory' but using a simple function.
    Initializes the provider-specific LangChain object.
    """
    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GEMINI_API_KEY,
            temperature=0.1,
            # Force JSON mode for Gemini 1.5+
            model_kwargs={"response_mime_type": "application/json"}
        )
    
    # Default to Ollama
    return ChatOllama(
        model=model_name,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
        format="json"  # Ollama's native JSON enforcement
    )

async def _run_chain(provider: str, model_name: str, prompt_text: str) -> Dict[str, Any]:
    """
    The actual execution logic. 
    Connects the prompt to the model and parses the JSON.
    """
    llm = _get_llm_instance(provider, model_name)
    
    # LangChain Expression Language (LCEL)
    prompt = ChatPromptTemplate.from_template("{input}")
    chain = prompt | llm | JsonOutputParser()

    return await chain.ainvoke({"input": prompt_text})

# --- DATA SANITIZATION ---

def sanitize_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures the LLM output matches the front-end and schema requirements."""
    if "diagram" in data:
        data["diagram"] = data["diagram"].replace("\n", " ").strip()

    valid_types = {
        "Service", "Gateway", "Queue", "Cache", "Storage", "CDN",
        "LoadBalancer", "Database", "Auth", "Monitor", "Search",
        "Worker", "Network", "Proxy"
    }
    
    normalized = []
    for comp in data.get("components", []):
        name = comp.get("name") or comp.get("id") or "Unknown"
        raw_type = comp.get("type", "Service")
        matched = next((t for t in valid_types if t.lower() in raw_type.lower()), "Service")
        normalized.append({"name": name, "type": matched})

    data["components"] = normalized
    return data

# --- MAIN SERVICE EXPORT ---

async def generate_architecture(
    query: str,
    provider: str = "gemini",
    constraints: Constraints = None,
    existing_diagram: str = None,
    existing_components: List[dict] = None,
    cached_constraints: dict = None,
) -> GenerateResponse:
    
    constraints = constraints or Constraints()
    is_refine = bool(existing_diagram)
    
    # 1. PREPARE THE PROMPT TEXT
    # We use 'prompt_text' consistently here
    if is_refine:
        c_str = json.dumps(cached_constraints or constraints.model_dump(exclude_none=True), indent=2)
        comp_str = json.dumps(existing_components or [], indent=2)
        prompt_text = get_refine_prompt(query, existing_diagram, comp_str, c_str)
    else:
        docs = get_relevant_docs(query, n_results=3)
        c_str = json.dumps(constraints.model_dump(exclude_none=True), indent=2)
        if docs:
            c_str += f"\n\nPRIORITY PATTERNS:\n{docs}"
        prompt_text = get_system_prompt(query, c_str)

    # 2. INITIAL MODEL SELECTION
    if provider == "gemini":
        model_name = "gemini-flash-latest" 
    else:
        model_name = "qwen2.5-coder:7b-instruct-q4_0"

    # 3. EXECUTION LOOP
    for attempt in range(2):
        try:
            print(f"[LLM] Attempting {model_name} via {provider}...")
            
            # Use 'prompt_text' which is defined above the loop
            raw_json = await _run_chain(provider, model_name, prompt_text)
            
            sanitized = sanitize_output(raw_json)
            return GenerateResponse(**sanitized)
                
        except Exception as e:
            print(f"[LLM] {provider} Error: {e}")
            
            # If Gemini fails (404, 503, or code error), pivot to Ollama
            if provider == "gemini":
                print(">>> 🚨 Pivoting to Local Ollama...")
                provider = "ollama"
                model_name = "qwen2.5-coder:7b-instruct-q4_0"
                # We do NOT redefine prompt_text; it's already in scope
                continue 
            
            # If Ollama also fails, we raise the final error
            raise e

    return build_fallback(query)
def build_fallback(query: str):
    return GenerateResponse(
        components=[{"name": "App", "type": "Service"}, {"name": "DB", "type": "Database"}],
        architecture="Standard fallback architecture.",
        scaling="Standard scaling.",
        diagram="graph TD; App-->DB;"
    )