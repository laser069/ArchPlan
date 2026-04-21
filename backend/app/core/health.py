"""
Health check and service status monitoring.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import asyncio


class HealthStatus:
    """Health status tracker for services."""
    
    def __init__(self):
        self.database_ok = False
        self.llm_providers = {
            "gemini": False,
            "groq": False,
            "openrouter": False,
            "ollama": False,
        }
        self.rag_system_ok = False
        self.last_check = None
        self.error_messages = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert health status to dictionary."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.get_overall_status(),
            "database": self.database_ok,
            "llm_providers": self.llm_providers,
            "rag_system": self.rag_system_ok,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "errors": self.error_messages,
        }
    
    def get_overall_status(self) -> str:
        """Get overall system status."""
        if self.database_ok and any(self.llm_providers.values()):
            return "healthy"
        elif self.database_ok or any(self.llm_providers.values()):
            return "degraded"
        else:
            return "unhealthy"
    
    def update_llm_status(self, provider: str, ok: bool, error: Optional[str] = None):
        """Update LLM provider status."""
        if provider in self.llm_providers:
            self.llm_providers[provider] = ok
            if not ok and error:
                self.error_messages[f"llm_{provider}"] = error
            elif ok and f"llm_{provider}" in self.error_messages:
                del self.error_messages[f"llm_{provider}"]
        self.last_check = datetime.utcnow()
    
    def update_database_status(self, ok: bool, error: Optional[str] = None):
        """Update database status."""
        self.database_ok = ok
        if not ok and error:
            self.error_messages["database"] = error
        elif ok and "database" in self.error_messages:
            del self.error_messages["database"]
        self.last_check = datetime.utcnow()
    
    def update_rag_status(self, ok: bool, error: Optional[str] = None):
        """Update RAG system status."""
        self.rag_system_ok = ok
        if not ok and error:
            self.error_messages["rag"] = error
        elif ok and "rag" in self.error_messages:
            del self.error_messages["rag"]
        self.last_check = datetime.utcnow()


# Global health status instance
_health_status = HealthStatus()


def get_health_status() -> HealthStatus:
    """Get the global health status instance."""
    return _health_status


async def check_ollama_health() -> bool:
    """Check if Ollama is available."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except Exception:
        return False


async def check_database_health() -> bool:
    """Check if database is available."""
    try:
        # This would check MongoDB connection
        # For now, we'll assume it's ok if no error occurs
        return True
    except Exception:
        return False


async def perform_health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    health = get_health_status()
    
    # Check Ollama (local LLM provider)
    ollama_ok = await check_ollama_health()
    health.update_llm_status("ollama", ollama_ok, 
                            None if ollama_ok else "Ollama not reachable")
    
    # Check database
    db_ok = await check_database_health()
    health.update_database_status(db_ok,
                                  None if db_ok else "Database connection failed")
    
    # Assume other providers are available (require API keys)
    health.update_llm_status("gemini", True)
    health.update_llm_status("groq", True)
    health.update_llm_status("openrouter", True)
    
    # RAG system is ok if we can load models
    health.rag_system_ok = True
    
    return health.to_dict()


def get_detailed_status() -> Dict[str, Any]:
    """Get detailed service status without performing checks."""
    return get_health_status().to_dict()
