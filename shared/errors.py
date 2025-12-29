"""
Standardized Error Handling for EconMind-Matrix

This module provides consistent error handling utilities across all layers.
It ensures a unified error response format and common error types.

Created as part of Technical Debt Issue #9 fix.

Usage:
    from shared.errors import APIError, NotFoundError, ValidationError
    
    # Raise standardized errors
    raise NotFoundError("Task", task_id)
    raise ValidationError("Terms list cannot be empty")
"""

from typing import Any, Optional
from fastapi import HTTPException
from fastapi.responses import JSONResponse


class APIError(HTTPException):
    """Base class for API errors with consistent structure."""
    
    def __init__(
        self, 
        status_code: int, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.error_code = error_code or f"ERR_{status_code}"
        self.message = message
        self.details = details
        super().__init__(
            status_code=status_code,
            detail={
                "error": True,
                "code": self.error_code,
                "message": message,
                "details": details
            }
        )


class NotFoundError(APIError):
    """Resource not found error (404)."""
    
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        if identifier is not None:
            message = f"{resource} '{identifier}' not found"
        super().__init__(
            status_code=404,
            message=message,
            error_code="NOT_FOUND"
        )


class ValidationError(APIError):
    """Validation error (400)."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            status_code=400,
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else None
        )


class ConflictError(APIError):
    """Conflict error - resource already exists or state conflict (409)."""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            status_code=409,
            message=message,
            error_code="CONFLICT",
            details={"resource": resource} if resource else None
        )


class ProcessingError(APIError):
    """Processing/server error (500)."""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        super().__init__(
            status_code=500,
            message=message,
            error_code="PROCESSING_ERROR",
            details={"operation": operation} if operation else None
        )


class UnauthorizedError(APIError):
    """Unauthorized access error (401)."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=401,
            message=message,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(APIError):
    """Forbidden access error (403)."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=403,
            message=message,
            error_code="FORBIDDEN"
        )


# Error response helper for consistency
def error_response(
    status_code: int,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Any] = None
) -> JSONResponse:
    """Create a consistent JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": True,
            "code": error_code or f"ERR_{status_code}",
            "message": message,
            "details": details
        }
    )


# Success response helper for consistency
def success_response(
    data: Any = None,
    message: Optional[str] = None
) -> dict:
    """Create a consistent success response structure."""
    response = {"success": True}
    if message:
        response["message"] = message
    if data is not None:
        response["data"] = data
    return response
