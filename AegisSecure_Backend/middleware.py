"""
Custom middleware for security, validation, and rate limiting.
"""
import time
import re
from typing import Callable
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from config import settings, SecurityHeaders


class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.cleanup_interval = 60  # Clean up old entries every 60 seconds
        self.last_cleanup = time.time()
    
    def _cleanup_old_requests(self):
        """Remove expired request timestamps to prevent memory leaks."""
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            for key in list(self.requests.keys()):
                self.requests[key] = [
                    req_time for req_time in self.requests[key]
                    if current_time - req_time < 3600  # Keep last hour
                ]
                if not self.requests[key]:
                    del self.requests[key]
            self.last_cleanup = current_time
    
    def is_rate_limited(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if the request should be rate limited.
        
        Args:
            identifier: Unique identifier (e.g., IP address or user ID)
            max_requests: Maximum number of requests allowed
            window_seconds: Time window in seconds
        
        Returns:
            True if rate limit exceeded, False otherwise
        """
        self._cleanup_old_requests()
        
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        # Filter out old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff_time
        ]
        
        if len(self.requests[identifier]) >= max_requests:
            return True
        
        self.requests[identifier].append(current_time)
        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on API endpoints."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Different rate limits for different endpoint types
        path = request.url.path
        
        # Strict rate limit for authentication endpoints
        if path.startswith("/auth/login") or path.startswith("/auth/register"):
            if rate_limiter.is_rate_limited(
                f"auth:{client_ip}",
                max_requests=settings.RATE_LIMIT_LOGIN_PER_HOUR,
                window_seconds=3600
            ):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Too many authentication attempts. Please try again later.",
                        "retry_after": 3600
                    }
                )
        
        # General rate limit for all other endpoints
        elif rate_limiter.is_rate_limited(
            f"general:{client_ip}",
            max_requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60
        ):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after": 60
                }
            )
        
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        for header, value in SecurityHeaders.HEADERS.items():
            response.headers[header] = value
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and sanitize requests."""
    
    SUSPICIOUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript injection
        r'on\w+\s*=',  # Event handlers
        r'SELECT.*FROM',  # SQL injection
        r'UNION.*SELECT',  # SQL injection
        r'DROP.*TABLE',  # SQL injection
        r'--',  # SQL comment
        r'/\*.*\*/',  # SQL comment
    ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Check content length to prevent large payload attacks
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request payload too large"}
            )
        
        # Validate query parameters for suspicious patterns
        for key, value in request.query_params.items():
            if self._contains_suspicious_pattern(value):
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": f"Invalid input in query parameter: {key}"}
                )
        
        response = await call_next(request)
        return response
    
    def _contains_suspicious_pattern(self, text: str) -> bool:
        """Check if text contains suspicious patterns."""
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        print(f"🔵 {request.method} {request.url.path} - Client: {client_ip}")
        
        try:
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            print(
                f"{status_emoji} {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration:.3f}s"
            )
            
            return response
        
        except Exception as e:
            duration = time.time() - start_time
            print(
                f"💥 {request.method} {request.url.path} - "
                f"Error: {str(e)} - Duration: {duration:.3f}s"
            )
            raise


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to catch and format unhandled errors."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except HTTPException:
            # Let FastAPI handle HTTPExceptions
            raise
        except Exception as e:
            # Log the error
            print(f"❌ Unhandled error in {request.url.path}: {str(e)}")
            
            # Return generic error response (don't expose internal details)
            if settings.DEBUG:
                detail = str(e)
            else:
                detail = "An internal error occurred. Please try again later."
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": detail,
                    "path": request.url.path,
                    "method": request.method
                }
            )


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    Handles proxy headers like X-Forwarded-For.
    """
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else "unknown"
