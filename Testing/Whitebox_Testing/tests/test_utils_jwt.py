"""
Tests for JWT utility functions
"""
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException
from utils.jwt_utils import (
    create_reset_jwt,
    decode_reset_jwt,
    decode_jwt,
    JWT_SECRET,
    JWT_ALGORITHM,
    RESET_JWT_TTL_MINUTES
)


class TestJWTConfiguration:
    """Test JWT configuration"""
    
    def test_jwt_secret_exists(self):
        """Test that JWT_SECRET is configured"""
        assert JWT_SECRET is not None
        assert len(JWT_SECRET) > 0
    
    def test_jwt_algorithm_is_hs256(self):
        """Test that JWT algorithm is HS256"""
        assert JWT_ALGORITHM == "HS256"
    
    def test_reset_jwt_ttl_is_positive(self):
        """Test that RESET_JWT_TTL_MINUTES is positive"""
        assert RESET_JWT_TTL_MINUTES > 0


class TestCreateResetJWT:
    """Test create_reset_jwt function"""
    
    def test_create_reset_jwt_returns_string(self):
        """Test that create_reset_jwt returns a string token"""
        token = create_reset_jwt("test@example.com")
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_reset_jwt_contains_email(self):
        """Test that created JWT contains the email"""
        email = "test@example.com"
        token = create_reset_jwt(email)
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == email
    
    def test_create_reset_jwt_has_purpose(self):
        """Test that created JWT has password_reset purpose"""
        token = create_reset_jwt("test@example.com")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert decoded["purpose"] == "password_reset"
    
    def test_create_reset_jwt_has_expiration(self):
        """Test that created JWT has expiration time"""
        token = create_reset_jwt("test@example.com")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert "exp" in decoded


class TestDecodeResetJWT:
    """Test decode_reset_jwt function"""
    
    def test_decode_valid_reset_jwt(self):
        """Test decoding valid reset JWT"""
        email = "test@example.com"
        token = create_reset_jwt(email)
        payload = decode_reset_jwt(token)
        assert payload["sub"] == email
        assert payload["purpose"] == "password_reset"
    
    def test_decode_reset_jwt_wrong_purpose(self):
        """Test decoding JWT with wrong purpose raises error"""
        # Create JWT with wrong purpose
        payload = {
            "sub": "test@example.com",
            "purpose": "something_else",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt(token)
        assert exc_info.value.status_code == 401
        assert "purpose" in exc_info.value.detail.lower()
    
    def test_decode_invalid_reset_jwt(self):
        """Test decoding invalid JWT raises error"""
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt("invalid.token.here")
        assert exc_info.value.status_code == 401


class TestDecodeJWT:
    """Test decode_jwt function"""
    
    def test_decode_valid_jwt(self):
        """Test decoding valid JWT"""
        payload = {"user_id": "123", "email": "test@example.com"}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        decoded = decode_jwt(token)
        assert decoded["user_id"] == "123"
        assert decoded["email"] == "test@example.com"
    
    def test_decode_expired_jwt(self):
        """Test decoding expired JWT raises error"""
        payload = {
            "user_id": "123",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_decode_invalid_jwt(self):
        """Test decoding invalid JWT raises error"""
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt("completely.invalid.token")
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()
    
    def test_decode_jwt_wrong_secret(self):
        """Test decoding JWT with wrong secret raises error"""
        payload = {"user_id": "123"}
        token = jwt.encode(payload, "wrong_secret", algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(token)
        assert exc_info.value.status_code == 401


class TestJWTEdgeCases:
    """Test edge cases for JWT utilities"""
    
    def test_create_reset_jwt_empty_email(self):
        """Test creating reset JWT with empty email"""
        token = create_reset_jwt("")
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == ""
    
    def test_create_reset_jwt_special_characters(self):
        """Test creating reset JWT with special characters in email"""
        email = "test+tag@example.com"
        token = create_reset_jwt(email)
        decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        assert decoded["sub"] == email
    
    def test_decode_jwt_no_expiration(self):
        """Test decoding JWT without expiration"""
        payload = {"user_id": "123"}
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        decoded = decode_jwt(token)
        assert decoded["user_id"] == "123"
