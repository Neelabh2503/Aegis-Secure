"""
Custom exception classes and error handling utilities.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

class AegisException(Exception):
    """Base exception class for AegisSecure application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(AegisException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

class AuthorizationError(AegisException):
    """Raised when user lacks permission."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )

class ValidationError(AegisException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class ResourceNotFoundError(AegisException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, resource: str = "Resource", details: Optional[Dict] = None):
        super().__init__(
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class DuplicateResourceError(AegisException):
    """Raised when attempting to create a duplicate resource."""
    
    def __init__(self, resource: str = "Resource", details: Optional[Dict] = None):
        super().__init__(
            message=f"{resource} already exists",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class DatabaseError(AegisException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

class ExternalAPIError(AegisException):
    """Raised when external API calls fail."""
    
    def __init__(
        self,
        service: str,
        message: str = "External API request failed",
        details: Optional[Dict] = None
    ):
        details = details or {}
        details["service"] = service
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )

class RateLimitError(AegisException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 60,
        details: Optional[Dict] = None
    ):
        details = details or {}
        details["retry_after"] = retry_after
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )

class OTPError(AegisException):
    """Raised when OTP operations fail."""
    
    def __init__(self, message: str = "OTP verification failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )

class TokenError(AegisException):
    """Raised when token operations fail."""
    
    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        JSONResponse with error details
    """
    content = {
        "error": True,
        "message": message,
        "status_code": status_code
    }
    
    if details:
        content["details"] = details
    
    return JSONResponse(status_code=status_code, content=content)

def handle_exception(exc: Exception) -> JSONResponse:
    """
    Convert exceptions to standardized JSON responses.
    
    Args:
        exc: Exception to handle
    
    Returns:
        JSONResponse with error details
    """
    if isinstance(exc, AegisException):
        return create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
    
    elif isinstance(exc, HTTPException):
        return create_error_response(
            message=exc.detail,
            status_code=exc.status_code
        )
    
    else:

        return create_error_response(
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details={"error_type": type(exc).__name__}
        )

class ErrorResponses:
    """Predefined error response templates."""
    
    @staticmethod
    def invalid_credentials():
        return create_error_response(
            message="Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def user_not_found():
        return create_error_response(
            message="User not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def email_already_exists():
        return create_error_response(
            message="Email already registered",
            status_code=status.HTTP_409_CONFLICT
        )
    
    @staticmethod
    def invalid_token():
        return create_error_response(
            message="Invalid or expired token",
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def weak_password():
        return create_error_response(
            message="Password does not meet security requirements",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "requirements": [
                    "At least 8 characters",
                    "At least one uppercase letter",
                    "At least one lowercase letter",
                    "At least one digit",
                    "At least one special character (@$!%*?&)"
                ]
            }
        )
    
    @staticmethod
    def otp_invalid():
        return create_error_response(
            message="Invalid or expired OTP",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    @staticmethod
    def rate_limit_exceeded(retry_after: int = 60):
        return create_error_response(
            message="Too many requests. Please try again later.",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details={"retry_after": retry_after}
        )
    
    @staticmethod
    def database_error():
        return create_error_response(
            message="Database operation failed. Please try again.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @staticmethod
    def external_api_error(service: str):
        return create_error_response(
            message=f"Failed to communicate with {service}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
