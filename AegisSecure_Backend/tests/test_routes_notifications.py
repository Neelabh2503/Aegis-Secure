"""
Unit tests for routes/notifications.py  
Tests notification handling and spam prediction.
"""
import pytest
from unittest.mock import patch, Mock
from .test_helpers import AsyncMock, AsyncContextManagerMock
from routes import notifications


class TestSpamPrediction:
    """Test spam prediction API calls."""
    
    @pytest.mark.asyncio
    async def test_get_spam_prediction_success(self):
        """Test successful spam prediction."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"final_decision": "spam", "confidence": "high"})
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        req = notifications.Spam_request(sender="test@example.com", subject="Test", text="Test message")
        with patch('httpx.AsyncClient', return_value=mock_context):
            result = await notifications.get_spam_prediction(req)
            assert isinstance(result, dict)
            assert result["final_decision"] == "spam"
    
    @pytest.mark.asyncio
    async def test_get_spam_prediction_ham(self):
        """Test ham (non-spam) prediction."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"final_decision": "ham", "confidence": "low"})
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        req = notifications.Spam_request(sender="friend@example.com", subject="Hi", text="Normal message")
        with patch('httpx.AsyncClient', return_value=mock_context):
            result = await notifications.get_spam_prediction(req)
            assert isinstance(result, dict)
            assert result["final_decision"] == "ham"
    
    @pytest.mark.asyncio
    async def test_get_spam_prediction_api_error(self):
        """Test spam prediction handles API errors."""
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(side_effect=Exception("API Error"))
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        req = notifications.Spam_request(sender="test@example.com", subject="Test", text="Test")
        with patch('httpx.AsyncClient', return_value=mock_context):
            result = await notifications.get_spam_prediction(req)
            assert isinstance(result, dict)
            assert result["final_decision"] == "unknown"
    
    @pytest.mark.asyncio
    async def test_get_spam_prediction_missing_field(self):
        """Test handling missing prediction field."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={})
        mock_response.raise_for_status = Mock()
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        req = notifications.Spam_request(sender="test@example.com", subject="Test", text="Test")
        with patch('httpx.AsyncClient', return_value=mock_context):
            result = await notifications.get_spam_prediction(req)
            assert isinstance(result, dict)


class TestAccessTokenRefresh:
    """Test Google access token refresh."""
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={"access_token": "new_token"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            token = await notifications.get_access_token_from_refresh("refresh")
            assert token == "new_token"
    
    @pytest.mark.asyncio
    async def test_refresh_token_failure(self):
        """Test token refresh failure."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            token = await notifications.get_access_token_from_refresh("invalid")
            assert token is None


class TestAnalyzeTextEndpoint:
    """Test text analysis endpoint."""
    
    @pytest.mark.asyncio
    async def test_analyze_text_with_valid_text(self):
        """Test analyzing valid text."""
        with patch('routes.notifications.get_spam_prediction', new_callable=AsyncMock, return_value="SPAM"):
            result = await notifications.analyze_text_endpoint({"text": "Buy now!!!"})
            assert "prediction" in result
    
    @pytest.mark.asyncio
    async def test_analyze_text_empty_text(self):
        """Test analyzing empty text."""
        result = await notifications.analyze_text_endpoint({"text": ""})
        assert result["prediction"] == "UNKNOWN"
    
    @pytest.mark.asyncio
    async def test_analyze_text_missing_text(self):
        """Test analyzing without text field."""
        result = await notifications.analyze_text_endpoint({})
        assert result["prediction"] == "UNKNOWN"
    
    @pytest.mark.asyncio
    async def test_analyze_text_exception_handling(self):
        """Test handling exceptions during analysis."""
        with patch('routes.notifications.get_spam_prediction', new_callable=AsyncMock, side_effect=Exception("API Error")), \
             patch('builtins.print'):
            result = await notifications.analyze_text_endpoint({"text": "Test"})
            assert result["prediction"] == "UNKNOWN"


class TestExtractBody:
    """Test email body extraction."""
    
    def test_extract_body_plain_text(self):
        """Test extracting plain text body."""
        import base64
        text = "Plain text email body"
        encoded = base64.urlsafe_b64encode(text.encode()).decode()
        
        payload = {
            "mimeType": "text/plain",
            "body": {"data": encoded}
        }
        
        result = notifications.extract_body(payload)
        assert result is not None
        assert "Plain text" in result
    
    def test_extract_body_html(self):
        """Test extracting HTML body."""
        import base64
        html = "<html><body>HTML email</body></html>"
        encoded = base64.urlsafe_b64encode(html.encode()).decode()
        
        payload = {
            "mimeType": "text/html",
            "body": {"data": encoded}
        }
        
        result = notifications.extract_body(payload)
        assert result is not None
        assert "HTML email" in result
    
    def test_extract_body_multipart(self):
        """Test extracting body from multipart."""
        import base64
        text = "Multipart message"
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
        
        result = notifications.extract_body(payload)
        assert result is not None
        assert "Multipart" in result
    
    def test_extract_body_none_payload(self):
        """Test handling None payload."""
        result = notifications.extract_body(None)
        assert result is None
    
    def test_extract_body_no_data(self):
        """Test payload without body data."""
        payload = {"mimeType": "text/plain", "body": {}}
        result = notifications.extract_body(payload)
        assert result is None
    
    def test_extract_body_invalid_encoding(self):
        """Test handling invalid base64."""
        payload = {
            "mimeType": "text/plain",
            "body": {"data": "invalid!!!base64"}
        }
        result = notifications.extract_body(payload)
        assert result is None


class TestGmailNotifications:
    """Test Gmail notification webhook."""
    
    @pytest.mark.asyncio
    async def test_notification_missing_message(self):
        """Test notification without message field."""
        mock_request = Mock()
        mock_request.json = AsyncMock(return_value={})
        
        result = await notifications.gmail_notifications(mock_request)
        assert result["status"] == "ignored"
    
    @pytest.mark.asyncio
    async def test_notification_missing_email_address(self):
        """Test notification without email address."""
        import base64
        import json
        
        msg_data = json.dumps({})
        encoded = base64.b64encode(msg_data.encode()).decode()
        
        mock_request = Mock()
        mock_request.json = AsyncMock(return_value={"message": {"data": encoded}})
        
        result = await notifications.gmail_notifications(mock_request)
        assert result["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_notification_user_not_found(self):
        """Test notification for non-existent user."""
        import base64
        import json
        
        msg_data = json.dumps({"emailAddress": "unknown@gmail.com", "historyId": "12345"})
        encoded = base64.b64encode(msg_data.encode()).decode()
        
        mock_request = Mock()
        mock_request.json = AsyncMock(return_value={"message": {"data": encoded}})
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=None):
            result = await notifications.gmail_notifications(mock_request)
            assert result["status"] == "ignored"
    
    @pytest.mark.asyncio
    async def test_notification_duplicate_history_id(self):
        """Test notification with duplicate history ID."""
        import base64
        import json
        
        msg_data = json.dumps({"emailAddress": "test@gmail.com", "historyId": "100"})
        encoded = base64.b64encode(msg_data.encode()).decode()
        
        mock_user = {
            "gmail_email": "test@gmail.com",
            "refresh_token": "refresh123",
            "last_history_id": "200"  # Higher than incoming
        }
        
        mock_request = Mock()
        mock_request.json = AsyncMock(return_value={"message": {"data": encoded}})
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            result = await notifications.gmail_notifications(mock_request)
            assert result["status"] == "duplicate"


class TestNotificationConfiguration:
    """Test notification module configuration."""
    
    def test_google_credentials_configured(self):
        """Test Google OAuth credentials are set."""
        assert notifications.GOOGLE_CLIENT_ID is not None
        assert notifications.GOOGLE_CLIENT_SECRET is not None
    
    def test_api_call_interval_configured(self):
        """Test API call interval is set."""
        assert notifications.API_CALL_INTERVAL > 0
    
    def test_router_exists(self):
        """Test notification router is configured."""
        assert notifications.router is not None


class TestSpamRequestModel:
    """Test Spam_request Pydantic model."""
    
    def test_spam_request_creation(self):
        """Test creating spam request."""
        req = notifications.Spam_request(
            sender="test@example.com",
            subject="Test Subject",
            text="Test body"
        )
        assert req.sender == "test@example.com"
        assert req.subject == "Test Subject"
        assert req.text == "Test body"


class TestNotificationsConfiguration:
    """Test notifications configuration."""
    
    def test_google_client_id_exists(self):
        """Test Google client ID is configured."""
        assert notifications.GOOGLE_CLIENT_ID is not None
    
    def test_google_client_secret_exists(self):
        """Test Google client secret is configured."""
        assert notifications.GOOGLE_CLIENT_SECRET is not None
    
    def test_redirect_uri_exists(self):
        """Test redirect URI is configured."""
        assert notifications.REDIRECT_URI is not None
    
    def test_cyber_secure_uri_exists(self):
        """Test CyberSecure API URI is configured."""
        assert notifications.CYBER_SECURE_URI is not None
        # Should be a valid URL
        assert "http" in notifications.CYBER_SECURE_URI.lower()


class TestGmailNotificationsEdgeCases:
    """Test gmail_notifications endpoint edge cases."""
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_ignored_no_message(self):
        """Test webhook ignored when message field missing."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={})
        
        result = await gmail_notifications(mock_request)
        assert result['status'] == 'ignored'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_missing_email_address(self):
        """Test webhook with missing emailAddress."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {"historyId": "12345"}
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        result = await gmail_notifications(mock_request)
        assert result['status'] == 'error'
        assert 'emailAddress' in result.get('message', '')
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_no_refresh_token(self):
        """Test webhook when user has no refresh token."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "12345"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {"gmail_email": "test@example.com", "user_id": "user123"}
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            result = await gmail_notifications(mock_request)
            assert result['status'] == 'ignored'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_duplicate_history_id(self):
        """Test webhook with duplicate historyId."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "100"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "refresh_token",
            "last_history_id": 100
        }
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            result = await gmail_notifications(mock_request)
            assert result['status'] == 'duplicate'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_token_refresh_fails(self):
        """Test webhook when token refresh fails."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "invalid_refresh",
            "last_history_id": 100
        }
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.notifications.get_access_token_from_refresh', new_callable=AsyncMock, return_value=None):
                result = await gmail_notifications(mock_request)
                assert result['status'] == 'error'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_empty_history(self):
        """Test webhook with empty history list."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "valid_refresh",
            "last_history_id": 100
        }
        
        mock_response = Mock()
        mock_response.json = Mock(return_value={"history": []})
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.notifications.get_access_token_from_refresh', new_callable=AsyncMock, return_value='access_token'):
                with patch('httpx.AsyncClient', return_value=mock_context):
                    mock_update = AsyncMock()
                    with patch('routes.notifications.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                        result = await gmail_notifications(mock_request)
                        assert result['status'] == 'empty'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_message_already_exists(self):
        """Test webhook when message already stored."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "valid_refresh",
            "last_history_id": 100
        }
        
        history_response = Mock()
        history_response.json = Mock(return_value={
            "history": [
                {
                    "messages": [
                        {"id": "msg123"}
                    ]
                }
            ]
        })
        
        existing_msg = {"gmail_id": "msg123", "from": "sender@example.com"}
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=history_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.notifications.get_access_token_from_refresh', new_callable=AsyncMock, return_value='access_token'):
                with patch('httpx.AsyncClient', return_value=mock_context):
                    with patch('routes.notifications.messages_col.find_one', new_callable=AsyncMock, return_value=existing_msg):
                        mock_update = AsyncMock()
                        with patch('routes.notifications.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                            result = await gmail_notifications(mock_request)
                            assert result['status'] == 'stored'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_message_no_sender(self):
        """Test webhook when message has no sender."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "valid_refresh",
            "last_history_id": 100
        }
        
        history_response = Mock()
        history_response.json = Mock(return_value={
            "history": [
                {
                    "messages": [
                        {"id": "msg123"}
                    ]
                }
            ]
        })
        
        msg_detail_response = Mock()
        msg_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": "Test snippet"
        })
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=[history_response, msg_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.notifications.get_access_token_from_refresh', new_callable=AsyncMock, return_value='access_token'):
                with patch('httpx.AsyncClient', return_value=mock_context):
                    with patch('routes.notifications.messages_col.find_one', new_callable=AsyncMock, return_value=None):
                        mock_update = AsyncMock()
                        with patch('routes.notifications.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                            result = await gmail_notifications(mock_request)
                            assert result['status'] == 'stored'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_message_no_body(self):
        """Test webhook when message has no body."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "valid_refresh",
            "last_history_id": 100
        }
        
        history_response = Mock()
        history_response.json = Mock(return_value={
            "history": [
                {
                    "messages": [
                        {"id": "msg123"}
                    ]
                }
            ]
        })
        
        msg_detail_response = Mock()
        msg_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": ""
        })
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=[history_response, msg_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.notifications.get_access_token_from_refresh', new_callable=AsyncMock, return_value='access_token'):
                with patch('httpx.AsyncClient', return_value=mock_context):
                    with patch('routes.notifications.messages_col.find_one', new_callable=AsyncMock, return_value=None):
                        with patch('routes.notifications.extract_body', return_value=None):
                            mock_update = AsyncMock()
                            with patch('routes.notifications.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                                result = await gmail_notifications(mock_request)
                                assert result['status'] == 'stored'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_body_truncation(self):
        """Test webhook truncates long message bodies."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        mock_user = {
            "gmail_email": "test@example.com",
            "user_id": "user123",
            "refresh_token": "valid_refresh",
            "last_history_id": 100
        }
        
        history_response = Mock()
        history_response.json = Mock(return_value={
            "history": [
                {
                    "messages": [
                        {"id": "msg123"}
                    ]
                }
            ]
        })
        
        long_body = "x" * 3000  # Body longer than 2000 chars
        
        msg_detail_response = Mock()
        msg_detail_response.json = Mock(return_value={
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test"}
                ]
            },
            "snippet": "snippet",
            "internalDate": "1234567890"
        })
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=[history_response, msg_detail_response])
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.notifications.get_access_token_from_refresh', new_callable=AsyncMock, return_value='access_token'):
                with patch('httpx.AsyncClient', return_value=mock_context):
                    with patch('routes.notifications.messages_col.find_one', new_callable=AsyncMock, return_value=None):
                        with patch('routes.notifications.extract_body', return_value=long_body):
                            mock_update = AsyncMock()
                            with patch('routes.notifications.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                                with patch('routes.notifications.accounts_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                                    result = await gmail_notifications(mock_request)
                                    assert result['status'] == 'stored'
    
    @pytest.mark.asyncio
    async def test_gmail_notifications_exception_handling(self):
        """Test webhook exception handling."""
        from routes.notifications import gmail_notifications
        from fastapi import Request
        import base64
        import json
        
        msg_data = {
            "emailAddress": "test@example.com",
            "historyId": "200"
        }
        encoded = base64.b64encode(json.dumps(msg_data).encode()).decode()
        
        mock_request = Mock(spec=Request)
        mock_request.json = AsyncMock(return_value={
            "message": {"data": encoded}
        })
        
        with patch('routes.notifications.accounts_col.find_one', new_callable=AsyncMock, side_effect=Exception("DB error")):
            result = await gmail_notifications(mock_request)
            assert result['status'] == 'error'
            assert 'DB error' in result['message']


class TestRetryFailedPredictions:
    """Test retry_failed_predictions background task."""
    
    @pytest.mark.asyncio
    async def test_retry_failed_predictions_no_messages(self):
        """Test when no messages need retry."""
        from routes.notifications import retry_failed_predictions
        import asyncio
        
        with patch('routes.notifications.messages_col.find_one_and_update', new_callable=AsyncMock, return_value=None):
            # Create a task and cancel after short delay
            task = asyncio.create_task(retry_failed_predictions())
            await asyncio.sleep(0.1)
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_retry_failed_predictions_missing_sender(self):
        """Test retry skips message without sender."""
        from routes.notifications import retry_failed_predictions
        import asyncio
        
        msg = {
            "_id": "msg123",
            "subject": "Test",
            "body": "Test body"
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.notifications.messages_col.find_one_and_update', new_callable=AsyncMock, side_effect=[msg, None]):
            with patch('routes.notifications.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                task = asyncio.create_task(retry_failed_predictions())
                await asyncio.sleep(0.1)
                task.cancel()
                
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    @pytest.mark.asyncio
    async def test_retry_failed_predictions_success(self):
        """Test successful prediction retry."""
        from routes.notifications import retry_failed_predictions
        import asyncio
        
        msg = {
            "_id": "msg123",
            "from": "sender@example.com",
            "subject": "Test",
            "body": "Test body",
            "gmail_id": "gmail123"
        }
        
        prediction = {
            "confidence": "spam",
            "reasoning": "Phishing attempt",
            "highlighted_text": "suspicious",
            "suggestion": "Delete",
            "final_decision": "spam"
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.notifications.messages_col.find_one_and_update', new_callable=AsyncMock, side_effect=[msg, None]):
            with patch('routes.notifications.get_spam_prediction', new_callable=AsyncMock, return_value=prediction):
                with patch('routes.notifications.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    task = asyncio.create_task(retry_failed_predictions())
                    await asyncio.sleep(0.1)
                    task.cancel()
                    
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
    
    @pytest.mark.asyncio
    async def test_retry_failed_predictions_exception(self):
        """Test retry handles exceptions."""
        from routes.notifications import retry_failed_predictions
        import asyncio
        
        msg = {
            "_id": "msg123",
            "from": "sender@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.notifications.messages_col.find_one_and_update', new_callable=AsyncMock, side_effect=[msg, None]):
            with patch('routes.notifications.get_spam_prediction', new_callable=AsyncMock, side_effect=Exception("API error")):
                with patch('routes.notifications.messages_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                    task = asyncio.create_task(retry_failed_predictions())
                    await asyncio.sleep(0.1)
                    task.cancel()
                    
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass


class TestCleanInvalidMessages:
    """Test clean_invalid_messages background task."""
    
    @pytest.mark.asyncio
    async def test_clean_invalid_messages_success(self):
        """Test cleaning invalid messages."""
        from routes.notifications import clean_invalid_messages
        import asyncio
        
        mock_delete_result = Mock(deleted_count=3)
        
        with patch('routes.notifications.messages_col.delete_many', new_callable=AsyncMock, return_value=mock_delete_result):
            task = asyncio.create_task(clean_invalid_messages())
            await asyncio.sleep(0.1)
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    @pytest.mark.asyncio
    async def test_clean_invalid_messages_exception(self):
        """Test clean handles exceptions."""
        from routes.notifications import clean_invalid_messages
        import asyncio
        
        with patch('routes.notifications.messages_col.delete_many', new_callable=AsyncMock, side_effect=Exception("DB error")):
            task = asyncio.create_task(clean_invalid_messages())
            await asyncio.sleep(0.1)
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass

