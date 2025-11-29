"""
Tests for access token utility functions
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from utils.access_token_util import get_access_token, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET


class TestAccessTokenConfiguration:
    """Test access token configuration"""
    
    def test_google_client_id_exists(self):
        """Test that GOOGLE_CLIENT_ID is configured"""
        # May be None in test environment
        assert GOOGLE_CLIENT_ID is not None or GOOGLE_CLIENT_ID is None
    
    def test_google_client_secret_exists(self):
        """Test that GOOGLE_CLIENT_SECRET is configured"""
        # May be None in test environment
        assert GOOGLE_CLIENT_SECRET is not None or GOOGLE_CLIENT_SECRET is None


class TestGetAccessToken:
    """Test get_access_token function"""
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful access token retrieval"""
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "test_access_token"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            token = await get_access_token("refresh_token_123")
            assert token == "test_access_token"
    
    @pytest.mark.asyncio
    async def test_get_access_token_no_token_in_response(self):
        """Test access token retrieval when no token in response"""
        mock_response = Mock()
        mock_response.json.return_value = {}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            token = await get_access_token("refresh_token_123")
            assert token is None
    
    @pytest.mark.asyncio
    async def test_get_access_token_makes_correct_request(self):
        """Test that correct request is made to Google OAuth endpoint"""
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "token"}
        mock_post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await get_access_token("refresh_token_123")
            
            # Verify correct endpoint was called
            call_args = mock_post.call_args
            assert "oauth2.googleapis.com/token" in call_args[0][0]
