"""
Tests for user info utility functions
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
from utils.user_info_utils import get_current_user_id


class TestGetCurrentUserId:
    """Test get_current_user_id function"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_success(self):
        """Test successful user ID extraction from token"""
        mock_payload = {"user_id": "user123", "email": "test@example.com"}
        
        with patch('utils.user_info_utils.decode_jwt', return_value=mock_payload):
            user_id = await get_current_user_id("valid_token")
            assert user_id == "user123"
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_missing_user_id(self):
        """Test error when user_id missing from token"""
        mock_payload = {"email": "test@example.com"}  # No user_id
        
        with patch('utils.user_info_utils.decode_jwt', return_value=mock_payload):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("token")
            assert exc_info.value.status_code == 401
            assert "user_id" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_invalid_token(self):
        """Test error with invalid token"""
        from jose import JWTError
        
        with patch('utils.user_info_utils.decode_jwt', side_effect=JWTError("Invalid")):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_id("invalid_token")
            assert exc_info.value.status_code == 401


class TestUserInfoUtilsEdgeCases:
    """Test edge cases for user info utilities"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_empty_user_id(self):
        """Test with empty user_id in payload"""
        mock_payload = {"user_id": "", "email": "test@example.com"}
        
        with patch('utils.user_info_utils.decode_jwt', return_value=mock_payload):
            with pytest.raises(HTTPException):
                await get_current_user_id("token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_null_user_id(self):
        """Test with null user_id in payload"""
        mock_payload = {"user_id": None, "email": "test@example.com"}
        
        with patch('utils.user_info_utils.decode_jwt', return_value=mock_payload):
            with pytest.raises(HTTPException):
                await get_current_user_id("token")
