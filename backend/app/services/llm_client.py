from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Configuration
GEMINI_KEY = "YOUR_GEMINI_KEY"

async def call_llm(provider: str, model_name: str, prompt_text: str):
    """Functional entry point for LLM calls."""
    
    if provider == "gemini":
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=GEMINI_KEY,
            temperature=0.1,
            model_kwargs={"response_mime_type": "application/json"}
        )
    elif provider == "ollama":
        llm = ChatOllama(
            model=model_name,
            temperature=0.1,
            format="json"
        )
    else:
        raise ValueError(f"Unknown provider: {provider}")

    # The Chain
    prompt = ChatPromptTemplate.from_template("{input}")
    chain = prompt | llm | JsonOutputParser()
    
    return await chain.ainvoke({"input": prompt_text})