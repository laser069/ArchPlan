"""
Custom exception classes and error handling utilities.
"""
from fastapi import HTTPException, status
from typing import Optional, Any


class ArchPlanException(Exception):
    """Base exception for ArchPlan application."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ArchPlanException):
    """Raised when request validation fails."""
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation Error",
                "message": self.message,
                "details": self.details
            }
        )


class ConstraintExtractionError(ArchPlanException):
    """Raised when constraint extraction fails."""
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Constraint Extraction Failed",
                "message": self.message,
                "details": self.details
            }
        )


class LLMError(ArchPlanException):
    """Raised when LLM call fails."""
    
    def __init__(self, message: str, provider: str = "", details: Optional[dict] = None):
        self.provider = provider
        super().__init__(message, details)
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "LLM Service Error",
                "message": self.message,
                "provider": self.provider,
                "details": self.details
            }
        )


class DatabaseError(ArchPlanException):
    """Raised when database operation fails."""
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Database Error",
                "message": self.message,
                "details": self.details
            }
        )


class NotFoundError(ArchPlanException):
    """Raised when resource is not found."""
    
    def to_http_exception(self) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Not Found",
                "message": self.message,
                "details": self.details
            }
        )


def validate_or_raise(condition: bool, message: str, error_class=ValidationError):
    """
    Helper function to validate a condition and raise exception if false.
    
    Args:
        condition: Condition to validate
        message: Error message
        error_class: Exception class to raise
        
    Raises:
        error_class: If condition is False
    """
    if not condition:
        raise error_class(message)
