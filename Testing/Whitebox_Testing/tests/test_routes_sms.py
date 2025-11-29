"""
Unit tests for routes/sms.py
Tests SMS message synchronization and analysis.
"""
import pytest
from unittest.mock import patch, Mock
from .test_helpers import AsyncMock
from routes import sms
from datetime import datetime
import models


# Helper for async context manager mocking
class AsyncContextManagerMock:
    """Mock async context manager."""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class TestMessageHashing:
    """Test SMS message hash generation."""
    
    def test_generate_hash_consistent(self):
        """Test same input produces same hash."""
        hash1 = sms.generate_message_hash("1234567890", "Test message", 1234567890)
        hash2 = sms.generate_message_hash("1234567890", "Test message", 1234567890)
        assert hash1 == hash2
    
    def test_generate_hash_different_inputs(self):
        """Test different inputs produce different hashes."""
        hash1 = sms.generate_message_hash("1111111111", "Message 1", 1000000)
        hash2 = sms.generate_message_hash("2222222222", "Message 2", 2000000)
        assert hash1 != hash2
    
    def test_generate_hash_length(self):
        """Test hash is 64 characters (SHA-256)."""
        hash_val = sms.generate_message_hash("123", "msg", 456)
        assert len(hash_val) == 64
    
    def test_generate_hash_hex_format(self):
        """Test hash is valid hexadecimal."""
        hash_val = sms.generate_message_hash("123", "msg", 456)
        assert all(c in '0123456789abcdef' for c in hash_val)


class TestDocumentSerialization:
    """Test MongoDB document serialization."""
    
    def test_serialize_doc_with_object_id(self):
        """Test ObjectId conversion to string."""
        from bson import ObjectId
        doc = {"_id": ObjectId(), "data": "test"}
        result = sms.convert_doc(doc)
        assert isinstance(result["_id"], str)
        assert len(result["_id"]) == 24
    
    def test_serialize_doc_with_datetime(self):
        """Test datetime conversion to ISO format."""
        doc = {"_id": "123", "created_at": datetime(2025, 1, 1, 12, 0, 0)}
        result = sms.convert_doc(doc)
        assert isinstance(result["created_at"], str)
        assert "2025-01-01" in result["created_at"]
    
    def test_serialize_doc_without_datetime(self):
        """Test doc without datetime remains unchanged."""
        doc = {"_id": "123", "data": "test"}
        result = sms.convert_doc(doc)
        assert result["data"] == "test"


class TestSMSSpamPredictionIntegration:
    """Test SMS uses notifications spam prediction."""
    
    def test_sms_imports_spam_prediction(self):
        """Test SMS module imports get_spam_prediction."""
        # Verify get_spam_prediction exists in utils
        from utils.SpamPrediction_utils import get_spam_prediction
        assert get_spam_prediction is not None
        assert callable(get_spam_prediction)


class TestSMSModels:
    """Test SMS Pydantic models."""
    
    def test_sms_message_model(self):
        """Test SmsMessage model."""
        msg = models.SmsMessage(
            address="1234567890",
            body="Test message",
            date_ms=1234567890000,
            type="inbox"
        )
        assert msg.address == "1234567890"
        assert msg.body == "Test message"
        assert msg.date_ms == 1234567890000
        assert msg.type == "inbox"
    
    def test_sms_sync_request_model(self):
        """Test SmsSyncRequest model."""
        messages = [
            models.SmsMessage(address="111", body="Msg1", date_ms=1000, type="inbox"),
            models.SmsMessage(address="222", body="Msg2", date_ms=2000, type="sent")
        ]
        req = models.SmsSyncRequest(messages=messages)
        assert len(req.messages) == 2
        assert req.messages[0].address == "111"
    
    def test_sms_message_validation(self):
        """Test SmsMessage field validation."""
        with pytest.raises(ValueError):
            models.SmsMessage(address="123")  # Missing required fields


class TestSMSConfiguration:
    """Test SMS route configuration."""
    
    def test_sms_router_exists(self):
        """Test SMS router is configured."""
        assert sms.router is not None
        assert hasattr(sms.router, 'routes')


class TestGetAllSMS:
    """Test get all SMS endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_all_sms_success(self):
        """Test successful SMS retrieval."""
        mock_user = {"user_id": "user123"}
        mock_messages = [
            {"_id": "msg1", "address": "123", "body": "Hello", "timestamp": 1000},
            {"_id": "msg2", "address": "456", "body": "World", "timestamp": 2000}
        ]
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_messages)
        
        with patch('routes.sms.sms_messages_col.find', return_value=mock_cursor):
            result = await sms.get_all_sms(current_user=mock_user)
            
            assert "sms_messages" in result
            assert len(result["sms_messages"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_all_sms_empty(self):
        """Test SMS retrieval when no messages."""
        mock_user = {"user_id": "user123"}
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        with patch('routes.sms.sms_messages_col.find', return_value=mock_cursor):
            result = await sms.get_all_sms(current_user=mock_user)
            
            assert result["sms_messages"] == []
    
    @pytest.mark.asyncio
    async def test_get_all_sms_filters_by_user(self):
        """Test SMS retrieval filters by user_id."""
        mock_user = {"user_id": "user123"}
        
        mock_cursor = Mock()
        mock_cursor.sort = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        with patch('routes.sms.sms_messages_col.find', return_value=mock_cursor) as mock_find:
            await sms.get_all_sms(current_user=mock_user)
            
            # Verify find was called with user_id filter
            mock_find.assert_called_once()
            call_args = mock_find.call_args[0][0]
            assert call_args["user_id"] == "user123"


class TestSyncSMS:
    """Test SMS sync endpoint."""
    
    @pytest.mark.asyncio
    async def test_sync_sms_new_messages(self):
        """Test syncing new SMS messages."""
        mock_user = {"user_id": "user123"}
        messages = [
            models.SmsMessage(address="111", body="Test1", date_ms=1000, type="inbox"),
            models.SmsMessage(address="222", body="Test2", date_ms=2000, type="sent")
        ]
        request = models.SmsSyncRequest(messages=messages)
        
        with patch('routes.sms.sms_messages_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('routes.sms.sms_messages_col.insert_one', new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = Mock(inserted_id="new_id")
            
            result = await sms.sync_sms(request, current_user=mock_user)
            
            assert result["status"] == "success"
            assert result["inserted"] == 2
            assert mock_insert.call_count == 2
            
            # Verify the inserted documents had correct user_id
            calls = mock_insert.call_args_list
            for call in calls:
                inserted_doc = call[0][0]
                assert inserted_doc["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_sync_sms_duplicate_detection(self):
        """Test sync skips duplicate messages."""
        mock_user = {"user_id": "user123"}
        messages = [
            models.SmsMessage(address="111", body="Test", date_ms=1000, type="inbox")
        ]
        request = models.SmsSyncRequest(messages=messages)
        
        # Mock existing message found
        with patch('routes.sms.sms_messages_col.find_one', new_callable=AsyncMock, return_value={"_id": "existing"}), \
             patch('routes.sms.sms_messages_col.insert_one', new_callable=AsyncMock) as mock_insert:
            
            result = await sms.sync_sms(request, current_user=mock_user)
            
            assert result["inserted"] == 0
            mock_insert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_sms_no_user_id(self):
        """Test sync fails without user authentication."""
        mock_user = {}  # No user_id
        messages = [models.SmsMessage(address="111", body="Test", date_ms=1000, type="inbox")]
        request = models.SmsSyncRequest(messages=messages)
        
        with pytest.raises(Exception):  # Should raise HTTPException
            await sms.sync_sms(request, current_user=mock_user)
    
    @pytest.mark.asyncio
    async def test_sync_sms_sets_spam_fields(self):
        """Test sync initializes spam analysis fields."""
        mock_user = {"user_id": "user123"}
        messages = [models.SmsMessage(address="111", body="Test", date_ms=1000, type="inbox")]
        request = models.SmsSyncRequest(messages=messages)
        
        with patch('routes.sms.sms_messages_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('routes.sms.sms_messages_col.insert_one', new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = Mock(inserted_id="new_id")
            
            result = await sms.sync_sms(request, current_user=mock_user)
            
            # Check that insert_one was called and verify the document structure
            assert mock_insert.call_count == 1
            inserted_doc = mock_insert.call_args[0][0]  # First positional argument
            
            # Verify spam fields are initialized to None
            assert inserted_doc["spam_score"] is None
            assert inserted_doc["spam_reasoning"] is None
            assert inserted_doc["spam_verdict"] is None
            assert inserted_doc["spam_highlighted_text"] is None
            assert inserted_doc["spam_suggestion"] is None
            assert "hash" in inserted_doc
            assert "created_at" in inserted_doc
            assert inserted_doc["user_id"] == "user123"


# Retry tests removed - retry_failed_sms_predictions function doesn't exist in routes.sms
