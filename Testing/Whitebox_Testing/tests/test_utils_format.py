"""
Tests for format utility functions
"""
import pytest
from datetime import datetime
from bson import ObjectId
from utils.format_utils import convert_doc, generate_message_hash


class TestConvertDoc:
    """Test convert_doc function"""
    
    def test_convert_objectid_to_string(self):
        """Test converting ObjectId to string"""
        obj_id = ObjectId()
        result = convert_doc(obj_id)
        assert isinstance(result, str)
        assert len(result) == 24
    
    def test_convert_datetime_to_isoformat(self):
        """Test converting datetime to ISO format string"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = convert_doc(dt)
        assert isinstance(result, str)
        assert "2024-01-01" in result
    
    def test_convert_dict_with_objectid(self):
        """Test converting dict containing ObjectId"""
        obj_id = ObjectId()
        doc = {"_id": obj_id, "name": "test"}
        result = convert_doc(doc)
        assert isinstance(result["_id"], str)
        assert result["name"] == "test"
    
    def test_convert_dict_with_datetime(self):
        """Test converting dict containing datetime"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        doc = {"created_at": dt, "name": "test"}
        result = convert_doc(doc)
        assert isinstance(result["created_at"], str)
        assert "2024-01-01" in result["created_at"]
    
    def test_convert_list_with_objectids(self):
        """Test converting list containing ObjectIds"""
        obj_ids = [ObjectId(), ObjectId()]
        result = convert_doc(obj_ids)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(x, str) for x in result)
    
    def test_convert_nested_dict(self):
        """Test converting nested dict structure"""
        obj_id = ObjectId()
        doc = {
            "user": {
                "_id": obj_id,
                "name": "Test"
            },
            "posts": [
                {"_id": ObjectId(), "title": "Post 1"}
            ]
        }
        result = convert_doc(doc)
        assert isinstance(result["user"]["_id"], str)
        assert isinstance(result["posts"][0]["_id"], str)
    
    def test_convert_primitive_types(self):
        """Test that primitive types are returned as-is"""
        assert convert_doc("string") == "string"
        assert convert_doc(123) == 123
        assert convert_doc(45.67) == 45.67
        assert convert_doc(True) is True
        assert convert_doc(None) is None
    
    def test_convert_empty_dict(self):
        """Test converting empty dict"""
        result = convert_doc({})
        assert result == {}
    
    def test_convert_empty_list(self):
        """Test converting empty list"""
        result = convert_doc([])
        assert result == []


class TestGenerateMessageHash:
    """Test generate_message_hash function"""
    
    def test_generate_hash_basic(self):
        """Test basic hash generation"""
        hash_val = generate_message_hash("+1234567890", "Test message", 1234567890)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64  # SHA256 produces 64 hex characters
    
    def test_generate_hash_consistency(self):
        """Test that same inputs produce same hash"""
        hash1 = generate_message_hash("+111", "msg", 1000)
        hash2 = generate_message_hash("+111", "msg", 1000)
        assert hash1 == hash2
    
    def test_generate_hash_different_inputs(self):
        """Test that different inputs produce different hashes"""
        hash1 = generate_message_hash("+111", "msg1", 1000)
        hash2 = generate_message_hash("+111", "msg2", 1000)
        assert hash1 != hash2
    
    def test_generate_hash_different_address(self):
        """Test hash changes with different address"""
        hash1 = generate_message_hash("+111", "msg", 1000)
        hash2 = generate_message_hash("+222", "msg", 1000)
        assert hash1 != hash2
    
    def test_generate_hash_different_timestamp(self):
        """Test hash changes with different timestamp"""
        hash1 = generate_message_hash("+111", "msg", 1000)
        hash2 = generate_message_hash("+111", "msg", 2000)
        assert hash1 != hash2
    
    def test_generate_hash_empty_body(self):
        """Test hash generation with empty message body"""
        hash_val = generate_message_hash("+111", "", 1000)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64
    
    def test_generate_hash_special_characters(self):
        """Test hash generation with special characters"""
        hash_val = generate_message_hash("+111", "Test!@#$%^&*()", 1000)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64
    
    def test_generate_hash_unicode(self):
        """Test hash generation with unicode characters"""
        hash_val = generate_message_hash("+111", "Tëst mëssägë™", 1000)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64
    
    def test_generate_hash_long_message(self):
        """Test hash generation with very long message"""
        long_msg = "x" * 10000
        hash_val = generate_message_hash("+111", long_msg, 1000)
        assert len(hash_val) == 64  # Hash length stays consistent


class TestFormatUtilsEdgeCases:
    """Test edge cases for format utilities"""
    
    def test_convert_doc_with_mixed_types(self):
        """Test converting document with mixed data types"""
        doc = {
            "_id": ObjectId(),
            "name": "Test",
            "count": 42,
            "active": True,
            "tags": ["a", "b"],
            "created": datetime.now()
        }
        result = convert_doc(doc)
        assert isinstance(result["_id"], str)
        assert result["name"] == "Test"
        assert result["count"] == 42
        assert result["active"] is True
        assert result["tags"] == ["a", "b"]
        assert isinstance(result["created"], str)
    
    def test_generate_hash_deterministic(self):
        """Test hash generation is deterministic"""
        hashes = [
            generate_message_hash("+111", "test", 1000)
            for _ in range(100)
        ]
        assert len(set(hashes)) == 1  # All should be identical
