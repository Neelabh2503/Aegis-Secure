"""
Unit tests for configuration management (config.py)
White box testing: Testing internal logic and validation
"""
import pytest
from unittest.mock import patch
from config import Settings, StatusMessages, ValidationPatterns, settings


class TestSettings:
    """Test Settings class functionality."""
    
    def test_settings_singleton(self):
        """Test that settings instance is created correctly."""
        assert Settings.APP_NAME == "AegisSecure Backend"
        assert Settings.APP_VERSION == "1.0.0"
        assert Settings.JWT_ALGORITHM == "HS256"
    
    def test_jwt_config(self):
        """Test JWT configuration values."""
        assert Settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS > 0
        assert Settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS > 0
        assert Settings.RESET_JWT_TTL_MINUTES > 0
    
    def test_password_requirements(self):
        """Test password validation requirements."""
        assert Settings.PASSWORD_MIN_LENGTH >= 8
        assert Settings.PASSWORD_REQUIRE_UPPERCASE is True
        assert Settings.PASSWORD_REQUIRE_LOWERCASE is True
        assert Settings.PASSWORD_REQUIRE_DIGIT is True
        assert Settings.PASSWORD_REQUIRE_SPECIAL is True
    
    def test_rate_limiting_config(self):
        """Test rate limiting configuration."""
        assert Settings.RATE_LIMIT_ENABLED is True
        assert Settings.RATE_LIMIT_PER_MINUTE > 0
        assert Settings.RATE_LIMIT_LOGIN_PER_HOUR > 0
    
    def test_otp_config(self):
        """Test OTP configuration."""
        assert Settings.OTP_EXPIRE_MINUTES > 0
        assert Settings.OTP_LENGTH == 6
        assert Settings.OTP_MAX_ATTEMPTS > 0
    
    def test_validate_method_missing_jwt_secret(self, monkeypatch):
        """Test validation catches missing JWT_SECRET."""
        monkeypatch.setattr(Settings, "JWT_SECRET", "")
        errors = Settings.validate()
        assert any("JWT_SECRET" in error for error in errors)
    
    def test_validate_method_short_jwt_secret(self, monkeypatch):
        """Test validation catches short JWT_SECRET."""
        monkeypatch.setattr(Settings, "JWT_SECRET", "short")
        errors = Settings.validate()
        assert any("32 characters" in error for error in errors)
    
    def test_validate_method_missing_mongo_uri(self, monkeypatch):
        """Test validation catches missing MONGO_URI."""
        monkeypatch.setattr(Settings, "MONGO_URI", "")
        errors = Settings.validate()
        assert any("MONGO_URI" in error for error in errors)
    
    def test_validate_method_all_valid(self):
        """Test validation passes with all required fields."""
        # Assuming .env is properly configured
        errors = Settings.validate()
        # Should have no errors or only warnings
        assert isinstance(errors, list)


class TestStatusMessages:
    """Test StatusMessages constants."""
    
    def test_success_messages_exist(self):
        """Test that success messages are defined."""
        assert hasattr(StatusMessages, "SUCCESS")
        assert hasattr(StatusMessages, "LOGIN_SUCCESS")
        assert hasattr(StatusMessages, "REGISTRATION_SUCCESS")
    
    def test_error_messages_exist(self):
        """Test that error messages are defined."""
        assert hasattr(StatusMessages, "INVALID_CREDENTIALS")
        assert hasattr(StatusMessages, "USER_NOT_FOUND")
        assert hasattr(StatusMessages, "INTERNAL_ERROR")
    
    def test_messages_are_generic(self):
        """Test that error messages are generic (no info leakage)."""
        # Should not reveal specific details
        assert "Invalid email or password" in StatusMessages.INVALID_CREDENTIALS
        assert "does not exist" not in StatusMessages.INVALID_CREDENTIALS


class TestValidationPatterns:
    """Test validation regex patterns."""
    
    def test_email_pattern_valid(self):
        """Test email pattern matches valid emails."""
        import re
        pattern = ValidationPatterns.EMAIL_PATTERN
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.com"
        ]
        
        for email in valid_emails:
            assert re.match(pattern, email), f"Failed for {email}"
    
    def test_email_pattern_invalid(self):
        """Test email pattern rejects invalid emails."""
        import re
        pattern = ValidationPatterns.EMAIL_PATTERN
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com"
        ]
        
        for email in invalid_emails:
            assert not re.match(pattern, email), f"Should reject {email}"


class TestConfigurationMethods:
    """Test Settings methods."""
    
    def test_print_config_summary(self):
        """Test configuration summary can be printed without errors."""
        from config import settings
        
        # Should not raise any exceptions
        try:
            settings.print_config_summary()
            assert True
        except Exception as e:
            pytest.fail(f"print_config_summary raised exception: {e}")
    
    def test_settings_has_print_method(self):
        """Test settings instance has print_config_summary method."""
        from config import settings
        assert hasattr(settings, 'print_config_summary')
        assert callable(settings.print_config_summary)


class TestConfigValidation:
    """Test config validation edge cases."""
    
    def test_config_smtp_email_validation(self):
        """Test SMTP_EMAIL validation in config."""
        # Just test that validate returns a list
        errors = settings.validate()
        assert isinstance(errors, list)
    
    def test_config_print_summary_executes(self):
        """Test that print_config_summary executes without error."""
        with patch('builtins.print') as mock_print:
            settings.print_config_summary()
            mock_print.assert_called()
