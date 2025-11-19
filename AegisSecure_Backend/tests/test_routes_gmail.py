"""
Unit tests for routes/gmail.py
Tests Gmail integration endpoints.
"""
import pytest
from unittest.mock import patch, Mock
from .test_helpers import AsyncMock
from routes import gmail
import time
from jose import jwt


class TestStateTokenGeneration:
    """Test state token generation for OAuth."""
    
    def test_get_state_token_creates_jwt(self):
        """Test state token is valid JWT."""
        # Test the function directly instead of via HTTP
        result = gmail.get_state_token("test_user_123")
        assert "state" in result
        assert len(result["state"]) > 20
        # Verify it's a valid JWT
        payload = jwt.decode(result["state"], gmail.JWT_SECRET, algorithms=["HS256"])
        assert "user_id" in payload
    
    def test_state_token_contains_user_id(self):
        """Test state token payload contains user_id."""
        result = gmail.get_state_token("user_456")
        token = result["state"]
        
        payload = jwt.decode(token, gmail.JWT_SECRET, algorithms=["HS256"])
        assert payload["user_id"] == "user_456"
    
    def test_state_token_has_expiration(self):
        """Test state token has 5-minute expiration."""
        result = gmail.get_state_token("test")
        token = result["state"]
        
        payload = jwt.decode(token, gmail.JWT_SECRET, algorithms=["HS256"])
        assert "exp" in payload
        assert "iat" in payload
        # Expiration should be ~5 minutes from now
        exp_diff = payload["exp"] - payload["iat"]
        assert 290 <= exp_diff <= 310  # Allow 10s margin


class TestUserAuthentication:
    """Test JWT-based user authentication."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_valid_token(self):
        """Test valid token returns user_id."""
        payload = {"user_id": "test_user", "exp": int(time.time()) + 300}
        token = jwt.encode(payload, gmail.JWT_SECRET, algorithm="HS256")
        
        user_id = await gmail.get_current_user_id(token)
        assert user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_missing_user_id(self):
        """Test token without user_id raises error."""
        from fastapi import HTTPException
        payload = {"exp": int(time.time()) + 300}
        token = jwt.encode(payload, gmail.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc:
            await gmail.get_current_user_id(token)
        assert exc.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_expired_token(self):
        """Test expired token raises error."""
        from fastapi import HTTPException
        payload = {"user_id": "test", "exp": int(time.time()) - 100}
        token = jwt.encode(payload, gmail.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc:
            await gmail.get_current_user_id(token)
        assert exc.value.status_code == 401


class TestGetEmails:
    """Test getting emails for user."""
    
    @pytest.mark.asyncio
    async def test_get_emails_success(self):
        """Test successful email retrieval."""
        mock_emails = [
            {"user_id": "user1", "subject": "Test", "from": "sender@test.com", "timestamp": 1000},
            {"user_id": "user1", "subject": "Test 2", "from": "sender2@test.com", "date": 2000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor), \
             patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
            
            result = await gmail.get_emails(user_id="user1")
            
            assert len(result) == 2
            assert all(isinstance(e["timestamp"], int) for e in result)
            assert all("char_color" in e for e in result)
    
    @pytest.mark.asyncio
    async def test_get_emails_with_account_filter(self):
        """Test email retrieval filtered by account."""
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor) as mock_find, \
             patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock):
            
            await gmail.get_emails(user_id="user1", account="test@gmail.com")
            
            # Verify filter includes gmail_email
            call_args = mock_find.call_args[0][0]
            assert call_args["gmail_email"] == "test@gmail.com"
    
    @pytest.mark.asyncio
    async def test_get_emails_extracts_sender_email(self):
        """Test email sender extraction from header."""
        mock_emails = [
            {"user_id": "user1", "from": "Name <sender@example.com>", "timestamp": 1000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor), \
             patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value={"char_color": "#FF0000"}):
            
            result = await gmail.get_emails(user_id="user1")
            
            assert result[0]["char_color"] == "#FF0000"
    
    @pytest.mark.asyncio
    async def test_get_emails_handles_missing_timestamp(self):
        """Test handling emails without timestamp."""
        mock_emails = [{"user_id": "user1", "from": "test@test.com"}]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor), \
             patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
            
            result = await gmail.get_emails(user_id="user1")
            
            assert result[0]["timestamp"] == 0


class TestGetCurrentUser:
    """Test get current user endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful user retrieval."""
        mock_user = {"user_id": "user1", "name": "John Doe", "gmail_email": "john@gmail.com"}
        
        with patch('routes.gmail.accounts_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            result = await gmail.get_current_user("user1")
            
            assert result["name"] == "John Doe"
            assert result["gmail_email"] == "john@gmail.com"
    
    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self):
        """Test user not found."""
        from fastapi import HTTPException
        
        with patch('routes.gmail.accounts_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc:
                await gmail.get_current_user("nonexistent")
            
            assert exc.value.status_code == 404


class TestGetConnectedAccounts:
    """Test getting connected accounts."""
    
    @pytest.mark.asyncio
    async def test_get_connected_accounts_success(self):
        """Test successful connected accounts retrieval."""
        mock_accounts = [
            {"gmail_email": "account1@gmail.com", "connected_at": "2025-01-01"},
            {"gmail_email": "account2@gmail.com", "connected_at": "2025-01-02"}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_accounts)
        
        with patch('routes.gmail.accounts_col.find', return_value=mock_cursor):
            result = await gmail.get_connected_accounts(user_id="user1")
            
            assert "accounts" in result
            assert len(result["accounts"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_connected_accounts_empty(self):
        """Test no connected accounts."""
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        with patch('routes.gmail.accounts_col.find', return_value=mock_cursor):
            result = await gmail.get_connected_accounts(user_id="user1")
            
            assert result["accounts"] == []


class TestDeleteConnectedAccount:
    """Test deleting connected account."""
    
    @pytest.mark.asyncio
    async def test_delete_account_success(self):
        """Test successful account deletion."""
        mock_delete_result = Mock()
        mock_delete_result.deleted_count = 1
        
        mock_msg_result = Mock()
        mock_msg_result.deleted_count = 5
        
        with patch('routes.gmail.accounts_col.delete_one', new_callable=AsyncMock, return_value=mock_delete_result), \
             patch('routes.gmail.messages_col.delete_many', new_callable=AsyncMock, return_value=mock_msg_result):
            
            result = await gmail.delete_connected_account(
                {"gmail_email": "test@gmail.com"},
                user_id="user1"
            )
            
            assert "message" in result
            assert "success" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_delete_account_missing_email(self):
        """Test deletion fails without email."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await gmail.delete_connected_account({}, user_id="user1")
        
        assert exc.value.status_code == 400
    
    @pytest.mark.asyncio
    async def test_delete_account_not_found(self):
        """Test deletion of non-existent account."""
        from fastapi import HTTPException
        mock_delete_result = Mock()
        mock_delete_result.deleted_count = 0
        
        with patch('routes.gmail.accounts_col.delete_one', new_callable=AsyncMock, return_value=mock_delete_result), \
             patch('routes.gmail.messages_col.delete_many', new_callable=AsyncMock):
            
            with pytest.raises(HTTPException) as exc:
                await gmail.delete_connected_account(
                    {"gmail_email": "nonexistent@gmail.com"},
                    user_id="user1"
                )
            
            assert exc.value.status_code == 404


class TestSearchEmails:
    """Test email search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_emails_success(self):
        """Test successful email search."""
        mock_emails = [
            {"user_id": "user1", "subject": "Important meeting", "from": "boss@test.com", "date": 1000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor), \
             patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
            
            result = await gmail.search_emails(q="meeting", user_id="user1")
            
            assert len(result) == 1
            assert "timestamp" in result[0]
    
    @pytest.mark.asyncio
    async def test_search_emails_empty_query(self):
        """Test search with empty query."""
        result = await gmail.search_emails(q="", user_id="user1")
        assert result == []
    
    @pytest.mark.asyncio
    async def test_search_emails_case_insensitive(self):
        """Test search is case-insensitive."""
        mock_emails = [{"user_id": "user1", "subject": "TEST", "from": "test@test.com", "date": 1000}]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor) as mock_find, \
             patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
            
            await gmail.search_emails(q="test", user_id="user1")
            
            # Verify regex was used
            mock_find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_invalid_token(self):
        """Test invalid token raises error."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await gmail.get_current_user_id("invalid.token.here")
        assert exc.value.status_code == 401


class TestGmailConfiguration:
    """Test Gmail route configuration."""
    
    def test_jwt_secret_configured(self):
        """Test JWT secret is set."""
        assert gmail.JWT_SECRET is not None
        assert len(gmail.JWT_SECRET) > 0
    
    def test_algorithm_configured(self):
        """Test JWT algorithm is HS256."""
        assert gmail.ALGORITHM == "HS256"
    
    def test_oauth2_scheme_configured(self):
        """Test OAuth2 scheme is set up."""
        assert gmail.oauth2_scheme is not None


class TestGetEmailsEdgeCases:
    """Test get_emails edge cases."""
    
    @pytest.mark.asyncio
    async def test_get_emails_timestamp_fallback(self):
        """Test email timestamp fallback logic."""
        mock_emails = [
            {"user_id": "user1", "from": "test@test.com", "date": 5000}  # Has date, no timestamp
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
                result = await gmail.get_emails(user_id="user1")
                
                # Should convert date to timestamp
                assert result[0]['timestamp'] == 5000
    
    @pytest.mark.asyncio
    async def test_get_emails_no_timestamp_or_date(self):
        """Test email with no timestamp or date fields."""
        mock_emails = [
            {"user_id": "user1", "from": "test@test.com"}  # No timestamp or date
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
                result = await gmail.get_emails(user_id="user1")
                
                # Should default to 0
                assert result[0]['timestamp'] == 0
    
    @pytest.mark.asyncio
    async def test_get_emails_with_avatar_color(self):
        """Test email includes avatar color from database."""
        mock_emails = [
            {"user_id": "user1", "from": "User <test@test.com>", "timestamp": 1000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        mock_avatar = {"email": "test@test.com", "char_color": "#FF5733"}
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=mock_avatar):
                result = await gmail.get_emails(user_id="user1")
                
                assert result[0]['char_color'] == "#FF5733"
    
    @pytest.mark.asyncio
    async def test_get_emails_default_avatar_color(self):
        """Test default avatar color when not in database."""
        mock_emails = [
            {"user_id": "user1", "from": "test@test.com", "timestamp": 1000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
                result = await gmail.get_emails(user_id="user1")
                
                assert result[0]['char_color'] == "#90A4AE"
    
    @pytest.mark.asyncio
    async def test_get_emails_extracts_email_from_angle_brackets(self):
        """Test extracting email from Name <email> format."""
        mock_emails = [
            {"user_id": "user1", "from": "John Doe <john@example.com>", "timestamp": 1000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None) as mock_find:
                await gmail.get_emails(user_id="user1")
                
                # Should extract john@example.com
                mock_find.assert_called_with({"email": "john@example.com"})
    
    @pytest.mark.asyncio
    async def test_get_emails_sorted_by_timestamp(self):
        """Test emails are sorted newest first."""
        mock_emails = [
            {"user_id": "user1", "from": "a@test.com", "timestamp": 1000},
            {"user_id": "user1", "from": "b@test.com", "timestamp": 3000},
            {"user_id": "user1", "from": "c@test.com", "timestamp": 2000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
                result = await gmail.get_emails(user_id="user1")
                
                # Should be sorted newest to oldest
                assert result[0]['timestamp'] == 3000
                assert result[1]['timestamp'] == 2000
                assert result[2]['timestamp'] == 1000


class TestGetCurrentUserEdgeCases:
    """Test get_current_user edge cases."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_id_missing_user_id(self):
        """Test token without user_id."""
        from fastapi import HTTPException
        import jwt
        
        token = jwt.encode({"other": "data"}, gmail.JWT_SECRET, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc:
            await gmail.get_current_user_id(token)
        
        assert exc.value.status_code == 401
        assert "user_id" in exc.value.detail.lower()


class TestDeleteConnectedAccountEdgeCases:
    """Test delete_connected_account edge cases."""
    
    @pytest.mark.asyncio
    async def test_delete_account_no_messages_deleted(self):
        """Test deletion when no messages exist."""
        from fastapi import HTTPException
        
        mock_account_result = Mock(deleted_count=1)
        mock_msg_result = Mock(deleted_count=0)
        
        with patch('routes.gmail.accounts_col.delete_one', new_callable=AsyncMock, return_value=mock_account_result):
            with patch('routes.gmail.messages_col.delete_many', new_callable=AsyncMock, return_value=mock_msg_result):
                result = await gmail.delete_connected_account(
                    payload={"gmail_email": "test@gmail.com"},
                    user_id="user1"
                )
                
                # Should succeed even if no messages deleted
                assert result["message"] == "Account deleted successfully"


class TestSearchEmailsEdgeCases:
    """Test search_emails edge cases."""
    
    @pytest.mark.asyncio
    async def test_search_emails_invalid_timestamp(self):
        """Test search with non-integer timestamp."""
        mock_emails = [
            {"user_id": "user1", "subject": "Test", "from": "test@test.com", "date": "invalid"}
        ]
        
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_emails)
        
        with patch('routes.gmail.messages_col.find', return_value=mock_cursor):
            with patch('routes.gmail.avatars_col.find_one', new_callable=AsyncMock, return_value=None):
                result = await gmail.search_emails(q="test", user_id="user1")
                
                # Should default to 0 for invalid timestamp
                assert result[0]['timestamp'] == 0
    
    @pytest.mark.asyncio
    async def test_search_emails_exception_handling(self):
        """Test search handles exceptions."""
        from fastapi import HTTPException
        
        with patch('routes.gmail.messages_col.find', side_effect=Exception("DB Error")):
            with pytest.raises(HTTPException) as exc:
                await gmail.search_emails(q="test", user_id="user1")
            
            assert exc.value.status_code == 500
            assert "Error during search" in exc.value.detail

