"""
Unit tests for error handling (errors.py)
White box testing: Testing exception hierarchy and error responses
"""
import pytest
from fastapi import status
from errors import (
    AegisException, ValidationError, AuthenticationError,
    AuthorizationError, ResourceNotFoundError, DuplicateResourceError,
    TokenError, OTPError, DatabaseError, RateLimitError,
    ExternalAPIError, create_error_response, handle_exception,
    ErrorResponses
)


class TestExceptionHierarchy:
    """Test custom exception classes."""
    
    def test_aegis_exception_base(self):
        """Test AegisException base class."""
        exc = AegisException("Test error")
        assert exc.message == "Test error"
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        exc = AuthenticationError("Invalid credentials")
        assert exc.message == "Invalid credentials"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError exception."""
        exc = ResourceNotFoundError("User")
        assert exc.message == "User not found"
        assert exc.status_code == status.HTTP_404_NOT_FOUND
    
    def test_duplicate_resource_error(self):
        """Test DuplicateResourceError exception."""
        exc = DuplicateResourceError("Email")
        assert exc.message == "Email already exists"
        assert exc.status_code == status.HTTP_409_CONFLICT
    
    def test_token_error(self):
        """Test TokenError exception."""
        exc = TokenError("Invalid token")
        assert exc.message == "Invalid token"
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_otp_error(self):
        """Test OTPError exception."""
        exc = OTPError("Invalid OTP")
        assert exc.message == "Invalid OTP"
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        exc = RateLimitError()
        assert "rate limit" in exc.message.lower()
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestErrorResponse:
    """Test error response creation."""
    
    def test_create_error_response_basic(self):
        """Test basic error response creation."""
        response = create_error_response("Test error", status.HTTP_400_BAD_REQUEST)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.body is not None
    
    def test_create_error_response_with_details(self):
        """Test error response with additional details."""
        response = create_error_response(
            "Test error",
            status.HTTP_400_BAD_REQUEST,
            details={"field": "email", "issue": "invalid format"}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_handle_exception(self):
        """Test exception handling function."""
        exc = ValidationError("Invalid input")
        response = handle_exception(exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestErrorResponses:
    """Test predefined error response templates."""
    
    def test_invalid_credentials_response(self):
        """Test invalid credentials error response."""
        response = ErrorResponses.invalid_credentials()
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_user_not_found_response(self):
        """Test user not found error response."""
        response = ErrorResponses.user_not_found()
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_email_already_exists_response(self):
        """Test email already exists error response."""
        response = ErrorResponses.email_already_exists()
        assert response.status_code == status.HTTP_409_CONFLICT
    
    def test_rate_limit_exceeded_response(self):
        """Test rate limit exceeded error response."""
        response = ErrorResponses.rate_limit_exceeded(60)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    def test_database_error_response(self):
        """Test database error response."""
        response = ErrorResponses.database_error()
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestAuthorizationErrorDefaults:
    """Test AuthorizationError with defaults."""
    
    def test_authorization_error_no_args(self):
        """Test AuthorizationError with no arguments uses defaults."""
        error = AuthorizationError()
        
        assert error.message == "Insufficient permissions"
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.details == {}
    
    def test_authorization_error_with_message_only(self):
        """Test AuthorizationError with message only."""
        error = AuthorizationError("Custom auth error")
        
        assert error.message == "Custom auth error"
        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.details == {}


class TestDatabaseErrorDefaults:
    """Test DatabaseError with defaults."""
    
    def test_database_error_no_args(self):
        """Test DatabaseError with no arguments uses defaults."""
        error = DatabaseError()
        
        assert error.message == "Database operation failed"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.details == {}
    
    def test_database_error_with_message_only(self):
        """Test DatabaseError with message only."""
        error = DatabaseError("Connection lost")
        
        assert error.message == "Connection lost"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.details == {}


class TestExternalAPIErrorDefaults:
    """Test ExternalAPIError defaults and service handling."""
    
    def test_external_api_error_service_only(self):
        """Test ExternalAPIError with service name only."""
        error = ExternalAPIError("TestService")
        
        assert "External API request failed" in error.message
        assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert error.details["service"] == "TestService"
    
    def test_external_api_error_with_custom_message(self):
        """Test ExternalAPIError with custom message."""
        error = ExternalAPIError("Gmail", "Rate limit exceeded")
        
        assert error.message == "Rate limit exceeded"
        assert error.details["service"] == "Gmail"


class TestErrorResponseHelpers:
    """Test error response helper functions."""
    
    def test_create_error_response_basic(self):
        """Test create_error_response with basic parameters."""
        from errors import create_error_response
        
        response = create_error_response("Test error", 400)
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Test error" in content
    
    def test_create_error_response_with_details(self):
        """Test create_error_response with details dict."""
        from errors import create_error_response
        
        response = create_error_response(
            "Validation failed",
            422,
            {"field": "email", "reason": "invalid format"}
        )
        
        assert response.status_code == 422
        content = response.body.decode()
        assert "Validation failed" in content
        assert "email" in content


class TestErrorResponsesWeakPassword:
    """Test weak_password static method."""
    
    def test_weak_password_response(self):
        """Test weak_password returns proper response with requirements."""
        from errors import ErrorResponses
        
        response = ErrorResponses.weak_password()
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Password does not meet security requirements" in content
        assert "At least 8 characters" in content
        assert "uppercase" in content
        assert "lowercase" in content
        assert "digit" in content
        assert "special character" in content


class TestErrorResponsesOTPInvalid:
    """Test otp_invalid static method."""
    
    def test_otp_invalid_response(self):
        """Test otp_invalid returns proper response."""
        from errors import ErrorResponses
        
        response = ErrorResponses.otp_invalid()
        
        assert response.status_code == 400
        content = response.body.decode()
        assert "Invalid or expired OTP" in content


class TestErrorResponsesInvalidToken:
    """Test invalid_token static method."""
    
    def test_invalid_token_response(self):
        """Test invalid_token returns proper response."""
        from errors import ErrorResponses
        
        response = ErrorResponses.invalid_token()
        
        assert response.status_code == 401
        content = response.body.decode()
        assert "Invalid or expired token" in content


class TestErrorResponsesExternalAPI:
    """Test external_api_error static method."""
    
    def test_external_api_error_response(self):
        """Test external_api_error with service name."""
        from errors import ErrorResponses
        
        response = ErrorResponses.external_api_error("Gmail API")
        
        assert response.status_code == 503
        content = response.body.decode()
        assert "Failed to communicate with Gmail API" in content


class TestHandleExceptionHTTPException:
    """Test handle_exception with HTTPException."""
    
    def test_handle_http_exception(self):
        """Test handle_exception converts HTTPException properly."""
        from errors import handle_exception
        from fastapi import HTTPException
        
        exc = HTTPException(status_code=403, detail="Forbidden access")
        response = handle_exception(exc)
        
        assert response.status_code == 403
        content = response.body.decode()
        assert "Forbidden access" in content


class TestHandleExceptionGenericException:
    """Test handle_exception with generic Exception."""
    
    def test_handle_generic_exception(self):
        """Test handle_exception handles unexpected exceptions."""
        from errors import handle_exception
        
        exc = ValueError("Something went wrong")
        response = handle_exception(exc)
        
        assert response.status_code == 500
        content = response.body.decode()
        assert "An unexpected error occurred" in content
        assert "ValueError" in content


class TestAegisExceptionWithDetails:
    """Test AegisException with details parameter."""
    
    def test_aegis_exception_with_none_details(self):
        """Test AegisException converts None details to empty dict."""
        from errors import AegisException
        
        exc = AegisException("Test error", details=None)
        
        assert exc.details == {}
    
    def test_aegis_exception_with_populated_details(self):
        """Test AegisException preserves provided details."""
        from errors import AegisException
        
        details = {"key": "value", "code": 123}
        exc = AegisException("Test error", details=details)
        
        assert exc.details == details
        assert exc.details["key"] == "value"
        assert exc.details["code"] == 123


class TestExternalAPIErrorDetailsHandling:
    """Test ExternalAPIError details handling."""
    
    def test_external_api_error_none_details(self):
        """Test ExternalAPIError converts None details to dict with service."""
        from errors import ExternalAPIError
        
        exc = ExternalAPIError("TestService", details=None)
        
        assert exc.details == {"service": "TestService"}
    
    def test_external_api_error_existing_details(self):
        """Test ExternalAPIError adds service to existing details."""
        from errors import ExternalAPIError
        
        exc = ExternalAPIError("TestService", details={"error_code": 500})
        
        assert exc.details["service"] == "TestService"
        assert exc.details["error_code"] == 500


class TestRateLimitErrorDetailsHandling:
    """Test RateLimitError details handling."""
    
    def test_rate_limit_error_none_details(self):
        """Test RateLimitError converts None details to dict with retry_after."""
        from errors import RateLimitError
        
        exc = RateLimitError(retry_after=120, details=None)
        
        assert exc.details == {"retry_after": 120}
    
    def test_rate_limit_error_existing_details(self):
        """Test RateLimitError adds retry_after to existing details."""
        from errors import RateLimitError
        
        exc = RateLimitError(retry_after=90, details={"user_id": "123"})
        
        assert exc.details["retry_after"] == 90
        assert exc.details["user_id"] == "123"
