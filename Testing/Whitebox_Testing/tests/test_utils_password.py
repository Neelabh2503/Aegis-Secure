"""
Tests for password utility functions
"""
import pytest
from utils.password_utils import hash_password, verify_password, pwd_context


class TestPasswordHashing:
    """Test password hashing functions"""
    
    def test_hash_password_returns_hash(self):
        """Test that hash_password returns a hashed string"""
        plain = "MyPassword123!"
        hashed = hash_password(plain)
        assert hashed != plain
        assert len(hashed) > 0
        assert isinstance(hashed, str)
    
    def test_hash_password_different_hashes_for_same_password(self):
        """Test that same password produces different hashes (salt)"""
        plain = "SamePassword123"
        hash1 = hash_password(plain)
        hash2 = hash_password(plain)
        assert hash1 != hash2  # Should be different due to salt
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        plain = "CorrectPassword123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        plain = "CorrectPassword123"
        wrong = "WrongPassword456"
        hashed = hash_password(plain)
        assert verify_password(wrong, hashed) is False
    
    def test_verify_password_empty_string(self):
        """Test password verification with empty password"""
        plain = ""
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
    
    def test_verify_password_special_characters(self):
        """Test password verification with special characters"""
        plain = "P@ssw0rd!#$%^&*()"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True


class TestPasswordContext:
    """Test password context configuration"""
    
    def test_pwd_context_exists(self):
        """Test that pwd_context is properly initialized"""
        assert pwd_context is not None
    
    def test_pwd_context_uses_pbkdf2_sha256(self):
        """Test that pwd_context uses pbkdf2_sha256 scheme"""
        schemes = pwd_context.schemes()
        assert "pbkdf2_sha256" in schemes
    
    def test_hash_format(self):
        """Test that hash follows expected format"""
        hashed = hash_password("test")
        # pbkdf2_sha256 hashes start with $pbkdf2-sha256$
        assert hashed.startswith("$pbkdf2")


class TestPasswordEdgeCases:
    """Test edge cases for password utilities"""
    
    def test_hash_very_long_password(self):
        """Test hashing very long password raises exception"""
        import passlib.exc
        plain = "a" * 10000
        # passlib has a max password size limit
        with pytest.raises(passlib.exc.PasswordSizeError):
            hash_password(plain)
    
    def test_hash_unicode_password(self):
        """Test hashing password with unicode characters"""
        plain = "Pässwörd™123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
    
    def test_verify_with_invalid_hash(self):
        """Test verification with malformed hash raises exception"""
        import passlib.exc
        plain = "password"
        invalid_hash = "not_a_valid_hash"
        # Invalid hash format should raise UnknownHashError
        with pytest.raises(passlib.exc.UnknownHashError):
            verify_password(plain, invalid_hash)
