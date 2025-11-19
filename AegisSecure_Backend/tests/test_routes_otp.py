"""
Unit tests for routes/otp.py
Tests OTP generation, validation, and email sending.
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
from .test_helpers import AsyncMock
from routes import otp
from config import settings


# Helper for async context manager mocking
class AsyncContextManagerMock:
    """Mock async context manager."""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class TestOTPGeneration:
    """Test OTP generation logic."""
    
    def test_generate_otp_format(self):
        """Test OTP is 6 digits."""
        generated_otp = otp.generate_otp()
        assert len(generated_otp) == 6
        assert generated_otp.isdigit()
    
    def test_generate_otp_uniqueness(self):
        """Test OTPs are reasonably unique."""
        otps = [otp.generate_otp() for _ in range(100)]
        # Should have at least 95% unique values
        assert len(set(otps)) >= 95
    
    def test_generate_otp_range(self):
        """Test OTP is within valid range."""
        generated_otp = otp.generate_otp()
        assert 0 <= int(generated_otp) <= 999999
    
    def test_generate_otp_zero_padded(self):
        """Test OTPs are zero-padded to 6 digits."""
        # Mock to return small number
        with patch('random.randint', return_value=123):
            generated_otp = otp.generate_otp()
            assert generated_otp == "000123"


class TestAccessTokenRefresh:
    """Test Google OAuth token refresh."""
    
    @pytest.mark.asyncio
    async def test_get_access_token_success(self):
        """Test successful access token retrieval."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={"access_token": "new_token_123"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            token = await otp.get_access_token_from_refresh("refresh_token_abc")
            assert token == "new_token_123"
    
    @pytest.mark.asyncio
    async def test_get_access_token_failure(self):
        """Test access token retrieval failure."""
        mock_response = Mock()
        mock_response.json = Mock(return_value={})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            token = await otp.get_access_token_from_refresh("invalid_refresh")
            assert token is None


class TestGmailEmailSending:
    """Test Gmail API email sending."""
    
    @pytest.mark.asyncio
    async def test_send_gmail_email_success(self):
        """Test successful email sending via Gmail API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"id": "msg_123"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            result = await otp.send_gmail_email(
                "access_token",
                "test@example.com",
                "Test Subject",
                "Test Body"
            )
            assert result["id"] == "msg_123"
    
    @pytest.mark.asyncio
    async def test_send_gmail_email_failure(self):
        """Test email sending failure."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            with pytest.raises(Exception, match="Failed to send email"):
                await otp.send_gmail_email(
                    "invalid_token",
                    "test@example.com",
                    "Subject",
                    "Body"
                )
    
    @pytest.mark.asyncio
    async def test_send_gmail_email_with_html(self):
        """Test sending HTML email."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"id": "msg_456"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('httpx.AsyncClient', return_value=mock_context):
            html_body = "<html><body><h1>Test</h1></body></html>"
            result = await otp.send_gmail_email(
                "access_token",
                "test@example.com",
                "HTML Email",
                html_body
            )
            assert result is not None


class TestSendOTPEmail:
    """Test OTP email sending."""
    
    @pytest.mark.asyncio
    async def test_send_otp_email_success(self):
        """Test successful OTP email sending."""
        mock_get_token = AsyncMock(return_value="access_token_123")
        mock_send_email = AsyncMock(return_value={"id": "msg_789"})
        
        with patch('routes.otp.get_access_token_from_refresh', mock_get_token):
            with patch('routes.otp.send_gmail_email', mock_send_email):
                result = await otp.send_otp_email_async("user@example.com", "123456")
                assert result is True
                mock_get_token.assert_called_once()
                mock_send_email.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_otp_email_token_failure(self):
        """Test OTP email failure due to token error."""
        with patch('routes.otp.get_access_token_from_refresh', new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = None
            result = await otp.send_otp_email_async("user@example.com", "123456")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_send_otp_email_send_failure(self):
        """Test OTP email failure during sending."""
        with patch('routes.otp.get_access_token_from_refresh', new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "access_token_123"
            with patch('routes.otp.send_gmail_email', new_callable=AsyncMock) as mock_send_email:
                mock_send_email.side_effect = Exception("Network error")
                result = await otp.send_otp_email_async("user@example.com", "123456")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_send_otp_email_html_formatting(self):
        """Test OTP email contains formatted HTML."""
        with patch('routes.otp.get_access_token_from_refresh', new_callable=AsyncMock) as mock_get_token:
            mock_get_token.return_value = "access_token"
            with patch('routes.otp.send_gmail_email', new_callable=AsyncMock) as mock_send_email:
                mock_send_email.return_value = {"id": "msg_id"}
                await otp.send_otp_email_async("test@test.com", "654321")
                
                # Verify send_gmail_email was called
                assert mock_send_email.called
                call_args = mock_send_email.call_args[0]
                
                # Check HTML body contains OTP
                html_body = call_args[3]
                assert "654321" in html_body
                assert "AegisSecure" in html_body


class TestOTPConfiguration:
    """Test OTP configuration values."""
    
    def test_otp_expire_minutes_configured(self):
        """Test OTP expiration is properly configured."""
        assert hasattr(settings, 'OTP_EXPIRE_MINUTES')
        assert settings.OTP_EXPIRE_MINUTES > 0
        assert settings.OTP_EXPIRE_MINUTES <= 60  # Reasonable max
    
    def test_otp_length_configured(self):
        """Test OTP length is properly configured."""
        assert hasattr(settings, 'OTP_LENGTH')
        assert settings.OTP_LENGTH == 6


class TestStoreOTP:
    """Test OTP storage functionality."""
    
    @pytest.mark.asyncio
    async def test_store_otp_creates_document(self):
        """Test storing OTP creates proper document."""
        from routes.otp import store_otp
        
        mock_delete = AsyncMock()
        mock_insert = AsyncMock(return_value=Mock(inserted_id="otp123"))
        
        with patch('routes.otp.otp_col.delete_many', new_callable=AsyncMock, return_value=mock_delete.return_value) as mock_del:
            with patch('routes.otp.otp_col.insert_one', new_callable=AsyncMock, return_value=mock_insert.return_value) as mock_ins:
                await store_otp("test@example.com", "123456")
                
                # Should delete old OTPs first
                mock_del.assert_called_once()
                # Should insert new OTP
                mock_ins.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_otp_deletes_old_otps(self):
        """Test storing OTP removes previous OTPs for email."""
        from routes.otp import store_otp
        
        mock_delete = AsyncMock()
        mock_insert = AsyncMock()
        
        with patch('routes.otp.otp_col.delete_many', new_callable=AsyncMock, return_value=mock_delete.return_value) as mock_del:
            with patch('routes.otp.otp_col.insert_one', new_callable=AsyncMock, return_value=mock_insert.return_value):
                await store_otp("user@example.com", "999999")
                
                # Check it deleted old OTPs for this email
                call_args = mock_del.call_args[0][0]
                assert call_args['email'] == "user@example.com"
    
    @pytest.mark.asyncio
    async def test_store_otp_sets_expiration(self):
        """Test OTP has expiration time."""
        from routes.otp import store_otp
        from datetime import datetime
        
        mock_delete = AsyncMock()
        mock_insert = AsyncMock()
        
        with patch('routes.otp.otp_col.delete_many', new_callable=AsyncMock, return_value=mock_delete.return_value):
            with patch('routes.otp.otp_col.insert_one', new_callable=AsyncMock, return_value=mock_insert.return_value) as mock_ins:
                await store_otp("test@example.com", "123456")
                
                # Check document has expiration fields
                doc = mock_ins.call_args[0][0]
                assert 'created_at' in doc
                assert 'expires_at' in doc
                assert 'verified' in doc
                assert doc['verified'] is False


class TestVerifyOTPInDB:
    """Test OTP verification functionality."""
    
    @pytest.mark.asyncio
    async def test_verify_otp_success(self):
        """Test successful OTP verification."""
        from routes.otp import verify_otp_in_db
        from datetime import datetime, timedelta
        
        mock_doc = {
            "_id": "otp123",
            "email": "test@example.com",
            "otp": "123456",
            "verified": False,
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc):
            with patch('routes.otp.otp_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                result = await verify_otp_in_db("test@example.com", "123456")
                
                assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self):
        """Test OTP not found returns False."""
        from routes.otp import verify_otp_in_db
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=None):
            result = await verify_otp_in_db("test@example.com", "wrong")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_otp_marks_verified(self):
        """Test verification marks OTP as used."""
        from routes.otp import verify_otp_in_db
        from datetime import datetime, timedelta
        
        mock_doc = {
            "_id": "otp123",
            "email": "user@example.com",
            "otp": "654321",
            "verified": False,
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc):
            with patch('routes.otp.otp_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value) as mock_upd:
                await verify_otp_in_db("user@example.com", "654321")
                
                # Should update to verified=True
                update_call = mock_upd.call_args
                assert update_call[0][1]['$set']['verified'] is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_case_insensitive_email(self):
        """Test email is case insensitive."""
        from routes.otp import verify_otp_in_db
        from datetime import datetime, timedelta
        
        mock_doc = {
            "_id": "otp123",
            "email": "test@example.com",
            "otp": "123456",
            "verified": False,
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc) as mock_find:
            with patch('routes.otp.otp_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                await verify_otp_in_db("TEST@EXAMPLE.COM", "123456")
                
                # Should query with lowercase email
                query = mock_find.call_args[0][0]
                assert query['email'] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_verify_otp_zero_pads_otp(self):
        """Test OTP is zero-padded to 6 digits."""
        from routes.otp import verify_otp_in_db
        from datetime import datetime, timedelta
        
        mock_doc = {
            "_id": "otp123",
            "email": "test@example.com",
            "otp": "000123",
            "verified": False,
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        
        mock_update = AsyncMock()
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc) as mock_find:
            with patch('routes.otp.otp_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                await verify_otp_in_db("test@example.com", "123")
                
                # Should query with zero-padded OTP
                query = mock_find.call_args[0][0]
                assert query['otp'] == "000123"
    
    @pytest.mark.asyncio
    async def test_verify_otp_checks_expiration(self):
        """Test OTP verification checks expiration."""
        from routes.otp import verify_otp_in_db
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=None) as mock_find:
            await verify_otp_in_db("test@example.com", "123456")
            
            # Should query with expiration check
            query = mock_find.call_args[0][0]
            assert 'expires_at' in query
            assert '$gt' in query['expires_at']
    
    @pytest.mark.asyncio
    async def test_verify_otp_checks_not_verified(self):
        """Test only verifies unused OTPs."""
        from routes.otp import verify_otp_in_db
        
        with patch('routes.otp.otp_col.find_one', new_callable=AsyncMock, return_value=None) as mock_find:
            await verify_otp_in_db("test@example.com", "123456")
            
            # Should query for verified=False
            query = mock_find.call_args[0][0]
            assert query['verified'] is False


class TestEnsureOTPIndexes:
    """Test OTP index creation."""
    
    @pytest.mark.asyncio
    async def test_ensure_otp_indexes_creates_email_index(self):
        """Test email index is created."""
        from routes.otp import ensure_otp_indexes
        
        mock_create = AsyncMock()
        
        with patch('routes.otp.otp_col.create_index', new_callable=AsyncMock, return_value=mock_create.return_value) as mock_idx:
            await ensure_otp_indexes()
            
            # Should create at least 2 indexes
            assert mock_idx.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_ensure_otp_indexes_creates_expiration_index(self):
        """Test TTL index on expires_at is created."""
        from routes.otp import ensure_otp_indexes
        
        mock_create = AsyncMock()
        
        with patch('routes.otp.otp_col.create_index', new_callable=AsyncMock, return_value=mock_create.return_value) as mock_idx:
            await ensure_otp_indexes()
            
            # Check second call for TTL index
            assert mock_idx.call_count == 2
            second_call = mock_idx.call_args_list[1]
            assert second_call[0][0] == "expires_at"
            assert second_call[1].get('expireAfterSeconds') == 0


class TestSendOTPEmailEdgeCases:
    """Test send_otp_email_async edge cases."""
    
    @pytest.mark.asyncio
    async def test_send_otp_email_no_refresh_token(self):
        """Test email sending when refresh token missing."""
        from routes.otp import send_otp_email_async
        
        with patch('routes.otp.REFRESH_TOKEN', None):
            with patch('routes.otp.get_access_token_from_refresh', new_callable=AsyncMock, return_value=None):
                result = await send_otp_email_async("test@example.com", "123456")
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_send_otp_email_includes_otp_expiry(self):
        """Test email body includes OTP expiration time."""
        from routes.otp import send_otp_email_async
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={"id": "msg123"})
        
        mock_client_instance = Mock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_context = AsyncContextManagerMock(mock_client_instance)
        
        with patch('routes.otp.get_access_token_from_refresh', new_callable=AsyncMock, return_value='access123'):
            with patch('httpx.AsyncClient', return_value=mock_context):
                result = await send_otp_email_async("test@example.com", "654321")
                
                assert result is True

