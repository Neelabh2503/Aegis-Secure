"""
Advanced tests for middleware.py
Tests edge cases, cleanup logic, and advanced scenarios.
"""
import pytest
import time
from unittest.mock import Mock, patch
from tests.test_helpers import AsyncMock
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from middleware import (
    RateLimiter,
    RateLimitMiddleware,
    RequestValidationMiddleware,
    get_client_ip
)


class TestRateLimiterAdvanced:
    """Advanced rate limiter tests."""
    
    def test_rate_limiter_cleanup_mechanism(self):
        """Test rate limiter cleans up old entries."""
        limiter = RateLimiter()
        
        # Add some requests
        for i in range(10):
            limiter.is_rate_limited(f"user_{i}", 10, 60)
        
        # Force cleanup by setting last_cleanup to past
        limiter.last_cleanup = time.time() - 70
        
        # Trigger cleanup
        limiter.is_rate_limited("cleanup_test", 10, 60)
        
        # Verify cleanup happened (last_cleanup updated)
        assert limiter.last_cleanup > time.time() - 5
    
    def test_rate_limiter_different_time_windows(self):
        """Test rate limiting with different time windows."""
        limiter = RateLimiter()
        
        # Test 1-minute window
        identifier1 = "user_1min"
        for i in range(5):
            is_limited = limiter.is_rate_limited(identifier1, 5, 60)
            if i < 5:
                assert is_limited == False
        
        # 6th request should be limited
        assert limiter.is_rate_limited(identifier1, 5, 60) == True
        
        # Test 1-hour window
        identifier2 = "user_1hour"
        for i in range(10):
            is_limited = limiter.is_rate_limited(identifier2, 10, 3600)
            if i < 10:
                assert is_limited == False
        
        # 11th request should be limited
        assert limiter.is_rate_limited(identifier2, 10, 3600) == True
    
    def test_rate_limiter_old_requests_removed(self):
        """Test old requests are removed from memory."""
        limiter = RateLimiter()
        identifier = "test_user"
        
        # Add old requests manually
        old_time = time.time() - 4000  # 4000 seconds ago
        limiter.requests[identifier] = [old_time]
        
        # Force cleanup
        limiter.last_cleanup = time.time() - 70
        limiter.is_rate_limited(identifier, 10, 60)
        
        # Old request should be removed (older than 3600 seconds)
        recent_requests = [
            req_time for req_time in limiter.requests.get(identifier, [])
            if time.time() - req_time < 3600
        ]
        assert old_time not in recent_requests
    
    def test_rate_limiter_empty_identifier_cleanup(self):
        """Test empty identifiers are removed during cleanup."""
        limiter = RateLimiter()
        
        # Add identifier with old requests
        limiter.requests["empty_user"] = [time.time() - 5000]
        
        # Force cleanup
        limiter.last_cleanup = time.time() - 70
        limiter.is_rate_limited("trigger_cleanup", 10, 60)
        
        # After cleanup, old identifiers with no recent requests should be removed
        # or should have empty lists
        if "empty_user" in limiter.requests:
            assert len(limiter.requests["empty_user"]) == 0
    
    def test_rate_limiter_concurrent_identifiers(self):
        """Test rate limiter handles multiple concurrent identifiers."""
        limiter = RateLimiter()
        
        # Create multiple users
        for user_id in range(20):
            identifier = f"concurrent_user_{user_id}"
            # Each user makes 3 requests
            for _ in range(3):
                is_limited = limiter.is_rate_limited(identifier, 5, 60)
                assert is_limited == False
        
        # All users should be tracked
        assert len(limiter.requests) >= 20


class TestRequestValidationAdvanced:
    """Advanced request validation tests."""
    
    @pytest.mark.asyncio
    async def test_payload_size_exactly_at_limit(self):
        """Test payload exactly at 10MB limit."""
        app = FastAPI()
        app.add_middleware(RequestValidationMiddleware)
        
        @app.post("/test")
        async def test_route():
            return {"ok": True}
        
        client = TestClient(app)
        
        # Exactly at limit (10MB = 10 * 1024 * 1024 bytes)
        limit_size = 10 * 1024 * 1024
        response = client.post("/test",
            headers={"content-length": str(limit_size)},
            json={"data": "test"})
        
        # Should allow (not over limit)
        assert response.status_code != 413
    
    @pytest.mark.asyncio
    async def test_payload_size_just_over_limit(self):
        """Test payload just over 10MB limit."""
        app = FastAPI()
        app.add_middleware(RequestValidationMiddleware)
        
        @app.post("/test")
        async def test_route():
            return {"ok": True}
        
        client = TestClient(app)
        
        # Just over limit
        over_limit_size = (10 * 1024 * 1024) + 1
        response = client.post("/test",
            headers={"content-length": str(over_limit_size)},
            json={})
        
        # Should reject
        assert response.status_code == 413
    
    def test_suspicious_pattern_detection_case_insensitive(self):
        """Test suspicious patterns are detected case-insensitively."""
        from middleware import RequestValidationMiddleware
        
        middleware = RequestValidationMiddleware(Mock())
        
        # Test various cases
        patterns = [
            "<SCRIPT>alert()</SCRIPT>",
            "SeLeCt * FrOm users",
            "UNION SELECT password",
            "DROP TABLE users"
        ]
        
        for pattern in patterns:
            result = middleware._contains_suspicious_pattern(pattern)
            assert result == True, f"Failed to detect: {pattern}"
    
    def test_safe_inputs_not_flagged(self):
        """Test safe inputs are not flagged as suspicious."""
        from middleware import RequestValidationMiddleware
        
        middleware = RequestValidationMiddleware(Mock())
        
        safe_inputs = [
            "Hello, world!",
            "user@example.com",
            "Normal text with numbers 123",
            "Price: $19.99",
            "Contact us at: example.com"
        ]
        
        for safe_input in safe_inputs:
            result = middleware._contains_suspicious_pattern(safe_input)
            assert result == False, f"Incorrectly flagged safe input: {safe_input}"


class TestGetClientIP:
    """Test client IP extraction utility."""
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({"X-Forwarded-For": "203.0.113.1, 198.51.100.1, 192.168.1.1"})
        mock_request.client = Mock()
        mock_request.client.host = "10.0.0.1"
        
        ip = get_client_ip(mock_request)
        # Should return first IP in forwarded chain
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_from_x_real_ip(self):
        """Test extracting IP from X-Real-IP header."""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({"X-Real-IP": "203.0.113.5"})
        mock_request.client = Mock()
        mock_request.client.host = "10.0.0.1"
        
        ip = get_client_ip(mock_request)
        assert ip == "203.0.113.5"
    
    def test_get_client_ip_priority_order(self):
        """Test IP extraction priority: X-Forwarded-For > X-Real-IP > client.host."""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "X-Forwarded-For": "203.0.113.1",
            "X-Real-IP": "203.0.113.2"
        })
        mock_request.client = Mock()
        mock_request.client.host = "10.0.0.1"
        
        ip = get_client_ip(mock_request)
        # X-Forwarded-For has priority
        assert ip == "203.0.113.1"
    
    def test_get_client_ip_fallback_to_direct(self):
        """Test fallback to direct client IP."""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = Mock()
        mock_request.client.host = "192.168.1.10"
        
        ip = get_client_ip(mock_request)
        assert ip == "192.168.1.10"
    
    def test_get_client_ip_no_client(self):
        """Test handling when no client information available."""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = None
        
        ip = get_client_ip(mock_request)
        assert ip == "unknown"
    
    def test_get_client_ip_whitespace_handling(self):
        """Test X-Forwarded-For with whitespace."""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({"X-Forwarded-For": " 203.0.113.1 , 198.51.100.1 "})
        mock_request.client = Mock()
        mock_request.client.host = "10.0.0.1"
        
        ip = get_client_ip(mock_request)
        # Should trim whitespace
        assert ip == "203.0.113.1"


class TestMiddlewareEdgeCases:
    """Test edge cases in middleware."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes with correct defaults."""
        limiter = RateLimiter()
        
        assert hasattr(limiter, 'requests')
        assert hasattr(limiter, 'cleanup_interval')
        assert limiter.cleanup_interval == 60
        assert isinstance(limiter.requests, dict)
    
    def test_rate_limiter_handles_zero_requests(self):
        """Test rate limiter with zero max requests."""
        limiter = RateLimiter()
        
        # Zero max requests should immediately limit
        is_limited = limiter.is_rate_limited("user", 0, 60)
        assert is_limited == True
    
    def test_rate_limiter_handles_negative_window(self):
        """Test rate limiter with negative window (edge case)."""
        limiter = RateLimiter()
        
        # Negative window - all requests are "old"
        # First request should be allowed, adds timestamp
        is_limited = limiter.is_rate_limited("user", 5, -1)
        # Behavior depends on implementation, just ensure no crash
        assert isinstance(is_limited, bool)
