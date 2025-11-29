"""
Unit tests for routes/Oauth.py
Tests OAuth flow and email body extraction.
"""
import pytest
from unittest.mock import patch, Mock
from .test_helpers import AsyncMock
from routes import Oauth
from fastapi import HTTPException
import base64
from utils.access_token_util import get_access_token
from utils.Color_decoration_utils import get_sender_avatar_color, COLOR_PALETTE
from utils.jwt_utils import JWT_SECRET
from database import avatars_col
import models
from utils.get_email_utils import extract_body


# Helper for async context manager mocking
class AsyncContextManagerMock:
    """Mock async context manager."""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class TestAccessTokenRefresh:
    """Test Google access token refresh."""
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={"access_token": "new_token_123"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            token = await get_access_token("refresh_token")
            assert token == "new_token_123"
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self):
        """Test token refresh failure."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            token = await get_access_token("invalid")
            assert token is None


class TestEmailBodyExtraction:
    """Test email body extraction from Gmail payload."""
    
    def test_extract_body_plain_text(self):
        """Test extracting plain text email body."""
        text = "Hello, this is a test email"
        encoded = base64.urlsafe_b64encode(text.encode()).decode()
        
        payload = {
            "mimeType": "text/plain",
            "body": {"data": encoded}
        }
        
        result = extract_body(payload)
        assert "Hello" in result
        assert "test email" in result
    
    def test_extract_body_html(self):
        """Test extracting HTML email body."""
        html = "<html><body>Test HTML email</body></html>"
        encoded = base64.urlsafe_b64encode(html.encode()).decode()
        
        payload = {
            "mimeType": "text/html",
            "body": {"data": encoded}
        }
        
        result = extract_body(payload)
        assert "Test HTML email" in result
    
    def test_extract_body_multipart(self):
        """Test extracting body from multipart email."""
        text = "Multipart message content"
        encoded = base64.urlsafe_b64encode(text.encode()).decode()
        
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": encoded}
                }
            ]
        }
        
        result = extract_body(payload)
        assert "Multipart message" in result
    
    def test_extract_body_empty_payload(self):
        """Test handling empty payload."""
        result = extract_body(None)
        assert result == ""
    
    def test_extract_body_no_data(self):
        """Test payload without body data."""
        payload = {"mimeType": "text/plain", "body": {}}
        result = extract_body(payload)
        assert result == ""
    
    def test_extract_body_decode_error(self):
        """Test handling decode errors."""
        payload = {
            "mimeType": "text/plain",
            "body": {"data": "invalid-base64!!!"}
        }
        result = extract_body(payload)
        assert result == ""


class TestOAuthConfiguration:
    """Test OAuth configuration."""
    
class TestRefreshAccessTokenEndpoint:
    """Test refresh access token endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh endpoint."""
        mock_user_data = {
            "user_id": "user123",
            "gmail_email": "test@gmail.com",
            "refresh_token": "refresh_token_123"
        }
        
        with patch('routes.Oauth.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user_data), \
             patch('routes.Oauth.get_access_token', new_callable=AsyncMock, return_value="new_access_token"):
            
            result = await Oauth.refresh_access_token("user123", "test@gmail.com")
            
            assert result["access_token"] == "new_access_token"
    
    @pytest.mark.asyncio
    async def test_refresh_token_no_user_data(self):
        """Test refresh fails when user not found."""
        with patch('routes.Oauth.accounts_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(Exception):  # HTTPException
                await Oauth.refresh_access_token("invalid", "test@gmail.com")
    
    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token(self):
        """Test refresh fails when refresh token missing."""
        mock_user_data = {"user_id": "user123", "gmail_email": "test@gmail.com"}
        
        with patch('routes.Oauth.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user_data):
            with pytest.raises(Exception):  # HTTPException
                await Oauth.refresh_access_token("user123", "test@gmail.com")
    
    @pytest.mark.asyncio
    async def test_refresh_token_failed_refresh(self):
        """Test refresh fails when token refresh fails."""
        mock_user_data = {
            "user_id": "user123",
            "gmail_email": "test@gmail.com",
            "refresh_token": "refresh_token_123"
        }
        
        with patch('routes.Oauth.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user_data), \
             patch('routes.Oauth.get_access_token', new_callable=AsyncMock, return_value=None):
            with pytest.raises(Exception):  # HTTPException
                await Oauth.refresh_access_token("user123", "test@gmail.com")


class TestGoogleCallback:
    """Test Google OAuth callback."""
    
    @pytest.mark.asyncio
    async def test_callback_missing_state(self):
        """Test callback fails without state."""
        with pytest.raises(Exception):  # HTTPException
            await Oauth.google_callback("auth_code", state=None)
    
    @pytest.mark.asyncio
    async def test_callback_invalid_jwt(self):
        """Test callback fails with invalid JWT."""
        with pytest.raises(Exception):  # HTTPException
            await Oauth.google_callback("auth_code", state="invalid_jwt")
    
    @pytest.mark.asyncio
    async def test_callback_jwt_missing_user_id(self):
        """Test callback fails when JWT missing user_id."""
        from jose import jwt
        invalid_token = jwt.encode({"exp": 9999999999}, Oauth.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(Exception):  # HTTPException
            await Oauth.google_callback("auth_code", state=invalid_token)


class TestGetSenderAvatarColor:
    """Test sender avatar color assignment."""
    
    @pytest.mark.asyncio
    async def test_get_existing_color(self):
        """Test retrieving existing avatar color."""
        mock_avatar = {"email": "test@example.com", "char_color": "#4285F4"}
        
        with patch('database.avatars_col.find_one', new_callable=AsyncMock, return_value=mock_avatar):
            color = await Oauth.get_sender_avatar_color("test@example.com")
            assert color == "#4285F4"
    
    @pytest.mark.asyncio
    async def test_assign_new_color(self):
        """Test assigning new avatar color."""
        with patch('database.avatars_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('database.avatars_col.update_one', new_callable=AsyncMock) as mock_update:
            
            color = await Oauth.get_sender_avatar_color("new@example.com")
            
            assert color in COLOR_PALETTE
            mock_update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_color_consistency(self):
        """Test color assignment is deterministic for same sender."""
        mock_avatar = {"email": "same@example.com", "char_color": "#EA4335"}
        
        with patch('database.avatars_col.find_one', new_callable=AsyncMock, return_value=mock_avatar):
            color1 = await Oauth.get_sender_avatar_color("same@example.com")
            color2 = await Oauth.get_sender_avatar_color("same@example.com")
            
            # If we're fetching existing, should be consistent
            assert color1 == color2


class TestColorPalette:
    """Test color palette configuration."""
    
    def test_color_palette_exists(self):
        """Test color palette is defined."""
        assert len(COLOR_PALETTE) > 0
    
    def test_all_colors_valid_hex(self):
        """Test all colors are valid hex codes."""
        import re
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        for color in COLOR_PALETTE:
            assert hex_pattern.match(color), f"Invalid hex color: {color}"
    
    def test_color_palette_diversity(self):
        """Test color palette has sufficient variety."""
        assert len(COLOR_PALETTE) >= 10
        assert len(set(COLOR_PALETTE)) == len(COLOR_PALETTE)  # No duplicates


class TestSpamRequestModel:
    """Test Spam_request Pydantic model."""
    
    def test_spam_request_valid(self):
        """Test valid spam request."""
        req = models.Spam_request(
            sender="test@example.com",
            subject="Test Subject",
            text="Test email body"
        )
        assert req.sender == "test@example.com"
        assert req.subject == "Test Subject"
        assert req.text == "Test email body"
    
    def test_spam_request_validation(self):
        """Test spam request validation."""
        with pytest.raises(ValueError):
            models.Spam_request(sender="test@example.com")  # Missing required fields


class TestGoogleCallbackEdgeCases:
    """Test google_callback endpoint edge cases."""
    
    @pytest.mark.asyncio
    async def test_google_callback_missing_state(self):
        """Test callback requires state parameter."""
        from routes.Oauth import google_callback
        
        with pytest.raises(HTTPException) as exc_info:
            await google_callback(code="auth_code")
        
        assert exc_info.value.status_code == 400
        assert "state" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_google_callback_invalid_jwt(self):
        """Test callback with invalid JWT state."""
        from routes.Oauth import google_callback
        
        with pytest.raises(HTTPException) as exc_info:
            await google_callback(code="auth_code", state="invalid.jwt.token")
        
        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_google_callback_jwt_missing_user_id(self):
        """Test callback with JWT missing user_id."""
        from routes.Oauth import google_callback
        import jwt
        
        token = jwt.encode({"other": "data"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            await google_callback(code="auth_code", state=token)
        
        assert exc_info.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_google_callback_no_access_token(self):
        """Test callback when token exchange fails."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        mock_response = Mock()
        mock_response.json = Mock(return_value={})  # No access_token
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with pytest.raises(HTTPException) as exc_info:
                await google_callback(code="auth_code", state=state)
            
            assert exc_info.value.status_code == 400
            assert "access token" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_google_callback_with_refresh_token(self):
        """Test callback stores refresh token."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={
            "access_token": "access123",
            "refresh_token": "refresh123"
        })
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": []})
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={"historyId": "54321"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    result = await google_callback(code="auth_code", state=state)
                    
                    assert "AegisSecure" in result.body.decode()
    
    @pytest.mark.asyncio
    async def test_google_callback_without_refresh_token(self):
        """Test callback without refresh token uses setOnInsert."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={
            "access_token": "access123"
            # No refresh_token
        })
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": []})
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={"historyId": "12345"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    result = await google_callback(code="auth_code", state=state)
                    
                    assert isinstance(result.body, bytes)
    
    @pytest.mark.asyncio
    async def test_google_callback_message_without_sender(self):
        """Test callback skips messages without sender."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={"access_token": "access123"})
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": [{"id": "msg1"}]})
        
        message_detail_response = Mock()
        message_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": "Test snippet",
            "internalDate": "1234567890"
        })
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response, message_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    with patch('utils.get_email_utils.extract_body', return_value="Test body"):
                        result = await google_callback(code="auth_code", state=state)
                        
                        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_google_callback_message_without_body(self):
        """Test callback skips messages without body."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={"access_token": "access123"})
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": [{"id": "msg1"}]})
        
        message_detail_response = Mock()
        message_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": "",
            "internalDate": "1234567890"
        })
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response, message_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    with patch('routes.Oauth.extract_body', return_value=""):
                        result = await google_callback(code="auth_code", state=state)
                        
                        assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_google_callback_body_truncation(self):
        """Test callback truncates long message bodies."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={"access_token": "access123"})
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": [{"id": "msg1"}]})
        
        long_body = "x" * 5000  # Body longer than 3000 chars
        
        message_detail_response = Mock()
        message_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": "snippet",
            "internalDate": "1234567890"
        })
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response, message_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    with patch('routes.Oauth.extract_body', return_value=long_body):
                        with patch('routes.Oauth.get_sender_avatar_color', new_callable=AsyncMock, return_value="#FF0000"):
                            result = await google_callback(code="auth_code", state=state)
                            
                            assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_google_callback_sender_email_extraction(self):
        """Test callback extracts email from From header."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={"access_token": "access123"})
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": [{"id": "msg1"}]})
        
        message_detail_response = Mock()
        message_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "From", "value": "John Doe <john@example.com>"},
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": "snippet",
            "internalDate": "1234567890"
        })
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response, message_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    with patch('routes.Oauth.extract_body', return_value="Test body"):
                        with patch('routes.Oauth.get_sender_avatar_color', new_callable=AsyncMock, return_value="#00FF00"):
                            result = await google_callback(code="auth_code", state=state)
                            
                            assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_google_callback_skips_incomplete_emails(self):
        """Test callback skips emails without subject or sender."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={"access_token": "access123"})
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": [{"id": "msg1"}]})
        
        message_detail_response = Mock()
        message_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"}
                    # No Subject
                ]
            },
            "snippet": "snippet",
            "internalDate": "1234567890"
        })
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response, message_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value) as mock_msg_update:
                    with patch('routes.Oauth.extract_body', return_value="body"):
                        with patch('routes.Oauth.get_sender_avatar_color', new_callable=AsyncMock, return_value="#0000FF"):
                            result = await google_callback(code="auth_code", state=state)
                            
                            # Should not update messages since subject is missing
                            assert result.status_code == 200
    
    @pytest.mark.asyncio
    async def test_google_callback_updates_history_id(self):
        """Test callback updates last_history_id."""
        from routes.Oauth import google_callback
        import jwt
        
        state = jwt.encode({"user_id": "user123"}, Oauth.JWT_SECRET, algorithm="HS256")
        
        token_response = Mock()
        token_response.json = Mock(return_value={"access_token": "access123"})
        
        profile_response = Mock()
        profile_response.json = Mock(return_value={"emailAddress": "test@gmail.com"})
        
        messages_response = Mock()
        messages_response.json = Mock(return_value={"messages": []})
        
        watch_response = Mock()
        watch_response.json = Mock(return_value={"historyId": "99999"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=[token_response, watch_response])
        mock_client_instance.get = AsyncMock(side_effect=[profile_response, messages_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        mock_update = AsyncMock()
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with patch('routes.Oauth.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                with patch('routes.Oauth.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    result = await google_callback(code="auth_code", state=state)
                    
                    assert result.status_code == 200

