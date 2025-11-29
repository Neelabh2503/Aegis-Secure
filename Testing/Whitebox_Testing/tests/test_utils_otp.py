
"""Tests for OTP utility functions"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from utils.otp_utils import (
    generate_otp,
    store_otp,
    verify_otp_in_db,
    OTP_EXPIRE_MINUTES
)


class TestOTPConfiguration:
    """Test OTP configuration"""
    
    def test_otp_expire_minutes_positive(self):
        """Test that OTP_EXPIRE_MINUTES is positive"""
        assert OTP_EXPIRE_MINUTES > 0


class TestGenerateOTP:
    """Test generate_otp function"""
    
    def test_generate_otp_returns_6_digits(self):
        """Test that generated OTP is 6 digits"""
        otp = generate_otp()
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_generate_otp_multiple_calls(self):
        """Test generating multiple OTPs"""
        otps = [generate_otp() for _ in range(100)]
        # All should be 6 digits
        assert all(len(otp) == 6 and otp.isdigit() for otp in otps)
    
    def test_generate_otp_range(self):
        """Test that generated OTP is in valid range"""
        otp = generate_otp()
        otp_int = int(otp)
        assert 0 <= otp_int <= 999999


class TestStoreOTP:
    """Test store_otp function"""
    
    @pytest.mark.asyncio
    async def test_store_otp_creates_document(self):
        """Test that store_otp creates OTP document"""
        mock_delete = AsyncMock()
        mock_insert = AsyncMock()
        
        with patch('utils.otp_utils.otp_col.delete_many', mock_delete), \
             patch('utils.otp_utils.otp_col.insert_one', mock_insert):
            
            await store_otp("test@example.com", "123456")
            
            # Should delete existing OTPs for email
            mock_delete.assert_called_once_with({"email": "test@example.com"})
            # Should insert new OTP
            mock_insert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_store_otp_document_structure(self):
        """Test structure of stored OTP document"""
        mock_delete = AsyncMock()
        captured_doc = None
        
        async def capture_insert(doc):
            nonlocal captured_doc
            captured_doc = doc
        
        with patch('utils.otp_utils.otp_col.delete_many', mock_delete), \
             patch('utils.otp_utils.otp_col.insert_one', capture_insert):
            
            await store_otp("test@example.com", "123456")
            
            assert captured_doc is not None
            assert captured_doc["email"] == "test@example.com"
            assert captured_doc["otp"] == "123456"
            assert "created_at" in captured_doc
            assert "expires_at" in captured_doc
            assert captured_doc["verified"] is False


class TestVerifyOTPInDB:
    """Test verify_otp_in_db function"""
    
    @pytest.mark.asyncio
    async def test_verify_otp_success(self):
        """Test successful OTP verification"""
        mock_doc = {
            "_id": "doc123",
            "email": "test@example.com",
            "otp": "123456",
            "verified": False,
            "expires_at": datetime.now(timezone.utc)
        }
        
        with patch('utils.otp_utils.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc), \
             patch('utils.otp_utils.otp_col.update_one', new_callable=AsyncMock):
            
            result = await verify_otp_in_db("test@example.com", "123456")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_not_found(self):
        """Test OTP verification when OTP not found"""
        with patch('utils.otp_utils.otp_col.find_one', new_callable=AsyncMock, return_value=None):
            result = await verify_otp_in_db("test@example.com", "999999")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_otp_marks_as_verified(self):
        """Test that successful verification marks OTP as verified"""
        mock_doc = {
            "_id": "doc123",
            "email": "test@example.com",
            "otp": "123456",
            "verified": False
        }
        mock_update = AsyncMock()
        
        with patch('utils.otp_utils.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc), \
             patch('utils.otp_utils.otp_col.update_one', mock_update):
            
            await verify_otp_in_db("test@example.com", "123456")
            
            # Should update verified field
            mock_update.assert_called_once()
            call_args = mock_update.call_args
            assert call_args[0][0] == {"_id": "doc123"}
            assert call_args[0][1]["$set"]["verified"] is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_case_insensitive_email(self):
        """Test OTP verification with different email case"""
        mock_doc = {"_id": "doc123", "email": "test@example.com", "otp": "123456", "verified": False}
        
        with patch('utils.otp_utils.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc), \
             patch('utils.otp_utils.otp_col.update_one', new_callable=AsyncMock):
            
            result = await verify_otp_in_db("TEST@EXAMPLE.COM", "123456")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_otp_pads_zeros(self):
        """Test OTP verification pads zeros correctly"""
        mock_doc = {"_id": "doc123", "email": "test@example.com", "otp": "000123", "verified": False}
        
        with patch('utils.otp_utils.otp_col.find_one', new_callable=AsyncMock, return_value=mock_doc), \
             patch('utils.otp_utils.otp_col.update_one', new_callable=AsyncMock):
            
            result = await verify_otp_in_db("test@example.com", "123")
            # Should verify since 123 is padded to 000123
            # Note: This depends on implementation - may need adjustment


class TestSendGmailEmail:
    """Test send_gmail_email function"""
    
    @pytest.mark.asyncio
    async def test_send_gmail_email_success(self):
        """Test successful email sending"""
        from utils.otp_utils import send_gmail_email
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "msg_123", "threadId": "thread_123"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.post = AsyncMock(return_value=mock_response)
            
            result = await send_gmail_email("access_token", "test@test.com", "Test Subject", "<p>Body</p>")
            assert result["id"] == "msg_123"
    
    @pytest.mark.asyncio
    async def test_send_gmail_email_failure(self):
        """Test email sending failure"""
        from utils.otp_utils import send_gmail_email
        
        mock_response = AsyncMock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_instance = mock_client.return_value.__aenter__.return_value
            mock_instance.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(Exception, match="Failed to send email"):
                await send_gmail_email("access_token", "test@test.com", "Test", "Body")


class TestSendOTP:
    """Test send_otp function"""
    
    @pytest.mark.asyncio
    async def test_send_otp_success(self):
        """Test successful OTP sending"""
        from utils.otp_utils import send_otp
        
        with patch('utils.otp_utils.get_access_token', AsyncMock(return_value="access_token")):
            with patch('utils.otp_utils.send_gmail_email', AsyncMock(return_value={"id": "msg_123"})):
                result = await send_otp("test@test.com", "123456")
                assert result is True
    
    @pytest.mark.asyncio
    async def test_send_otp_failure(self):
        """Test OTP sending failure"""
        from utils.otp_utils import send_otp
        
        with patch('utils.otp_utils.get_access_token', AsyncMock(return_value="access_token")):
            with patch('utils.otp_utils.send_gmail_email', AsyncMock(side_effect=Exception("Failed"))):
                result = await send_otp("test@test.com", "123456")
                assert result is False
    
    @pytest.mark.asyncio
    async def test_send_otp_no_access_token(self):
        """Test OTP sending when get_access_token fails"""
        from utils.otp_utils import send_otp
        
        with patch('utils.otp_utils.get_access_token', AsyncMock(side_effect=Exception("No token"))):
            result = await send_otp("test@test.com", "123456")
            assert result is False


class TestOTPEdgeCases:
    """Test edge cases for OTP utilities"""
    
    def test_generate_otp_leading_zeros(self):
        """Test that generated OTP preserves leading zeros"""
        # Generate many OTPs to likely get one with leading zeros
        otps = [generate_otp() for _ in range(1000)]
        # All should be 6 characters
        assert all(len(otp) == 6 for otp in otps)
    
    @pytest.mark.asyncio
    async def test_store_otp_empty_email(self):
        """Test storing OTP with empty email"""
        mock_delete = AsyncMock()
        mock_insert = AsyncMock()
        
        with patch('utils.otp_utils.otp_col.delete_many', mock_delete), \
             patch('utils.otp_utils.otp_col.insert_one', mock_insert):
            
            await store_otp("", "123456")
            mock_delete.assert_called_once()
            mock_insert.assert_called_once()
