"""
Logging configuration and utilities for structured logging.
"""
import logging
import json
from datetime import datetime
from typing import Any, Optional
import sys

# Create logger
logger = logging.getLogger("archplan")


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def configure_logging(debug: bool = False) -> None:
    """
    Configure application logging with JSON formatting.
    
    Args:
        debug: Enable debug level logging if True
    """
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())
    
    logger.addHandler(console_handler)


def log_request(method: str, path: str, provider: str = "", model: str = "") -> None:
    """Log API request."""
    logger.info(f"API Request: {method} {path}", extra={
        "event": "api_request",
        "method": method,
        "path": path,
        "provider": provider,
        "model": model,
    })


def log_response(status_code: int, duration_ms: float, provider: str = "") -> None:
    """Log API response."""
    logger.info(f"API Response: {status_code}", extra={
        "event": "api_response",
        "status_code": status_code,
        "duration_ms": duration_ms,
        "provider": provider,
    })


def log_llm_call(provider: str, model: str, duration_ms: float, tokens: Optional[int] = None) -> None:
    """Log LLM API call."""
    logger.info(f"LLM Call: {provider} ({model})", extra={
        "event": "llm_call",
        "provider": provider,
        "model": model,
        "duration_ms": duration_ms,
        "tokens": tokens,
    })


def log_error(error: Exception, context: str = "") -> None:
    """Log error with context."""
    logger.error(f"Error: {context}", exc_info=error, extra={
        "event": "error",
        "error_type": type(error).__name__,
        "context": context,
    })


def log_database_operation(operation: str, collection: str, result: Any) -> None:
    """Log database operation."""
    logger.info(f"DB Operation: {operation} on {collection}", extra={
        "event": "database_operation",
        "operation": operation,
        "collection": collection,
        "success": result is not None,
    })


def log_constraint_extraction(query_length: int, extracted_fields: int) -> None:
    """Log constraint extraction."""
    logger.info(f"Constraint Extraction: {extracted_fields} fields from {query_length} char query", extra={
        "event": "constraint_extraction",
        "query_length": query_length,
        "extracted_fields": extracted_fields,
    })
