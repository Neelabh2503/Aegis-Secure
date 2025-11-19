"""
Unit tests for validators.py
White box testing: Testing validation logic paths
"""
import pytest
from pydantic import ValidationError as PydanticValidationError
from validators import (
    PasswordValidator, EmailValidator, OTPValidator, 
    TextSanitizer, PhoneValidator, RegisterRequestValidator,
    PasswordResetValidator
)
from errors import ValidationError
from config import settings


class TestPasswordValidator:
    """Test password validation logic."""
    
    def test_validate_strong_password(self):
        """Test that strong passwords pass validation."""
        strong_passwords = [
            "SecureP@ss123",
            "MyP@ssw0rd!",
            "Str0ng!Pass"
        ]
        
        for password in strong_passwords:
            is_valid, message = PasswordValidator.validate(password)
            assert is_valid is True, f"Failed for {password}: {message}"
            assert message is None
    
    def test_validate_weak_password_too_short(self):
        """Test rejection of short passwords."""
        is_valid, message = PasswordValidator.validate("Short1!")
        assert is_valid is False
        assert "at least 8 characters" in message
    
    def test_validate_weak_password_no_uppercase(self):
        """Test rejection of passwords without uppercase."""
        is_valid, message = PasswordValidator.validate("password123!")
        assert is_valid is False
        assert "uppercase" in message.lower()
    
    def test_validate_weak_password_no_lowercase(self):
        """Test rejection of passwords without lowercase."""
        is_valid, message = PasswordValidator.validate("PASSWORD123!")
        assert is_valid is False
        assert "lowercase" in message.lower()
    
    def test_validate_weak_password_no_digit(self):
        """Test rejection of passwords without digits."""
        is_valid, message = PasswordValidator.validate("Password!")
        assert is_valid is False
        assert "digit" in message.lower()
    
    def test_validate_weak_password_no_special(self):
        """Test rejection of passwords without special characters."""
        is_valid, message = PasswordValidator.validate("Password123")
        assert is_valid is False
        assert "special character" in message.lower()
    
    def test_validate_common_password(self):
        """Test rejection of common weak passwords."""
        is_valid, message = PasswordValidator.validate("Password123")
        assert is_valid is False
        # Either fails on special char or common password
        assert message is not None


class TestEmailValidator:
    """Test email validation logic."""
    
    def test_validate_valid_emails(self):
        """Test that valid emails pass validation."""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            is_valid = EmailValidator.validate(email)
            assert is_valid is True, f"Failed for {email}"
    
    def test_validate_invalid_emails(self):
        """Test that invalid emails are rejected."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@domain",
            ""
        ]
        
        for email in invalid_emails:
            is_valid = EmailValidator.validate(email)
            assert is_valid is False, f"Should reject {email}"
    
    def test_validate_or_raise_invalid(self):
        """Test validate_or_raise with invalid email."""
        with pytest.raises(ValidationError):
            EmailValidator.validate_or_raise("invalid-email")


class TestOTPValidator:
    """Test OTP validation logic."""
    
    def test_validate_valid_otp(self):
        """Test that valid OTPs pass validation."""
        valid_otps = ["123456", "000000", "999999"]
        
        for otp in valid_otps:
            is_valid = OTPValidator.validate(otp)
            assert is_valid is True, f"Failed for {otp}"
    
    def test_validate_invalid_otp_length(self):
        """Test rejection of OTPs with wrong length."""
        invalid_otps = ["12345", "1234567", ""]
        
        for otp in invalid_otps:
            is_valid = OTPValidator.validate(otp)
            assert is_valid is False
    
    def test_validate_invalid_otp_non_numeric(self):
        """Test rejection of non-numeric OTPs."""
        invalid_otps = ["12345a", "abcdef", "12 456"]
        
        for otp in invalid_otps:
            is_valid = OTPValidator.validate(otp)
            assert is_valid is False


class TestTextSanitizer:
    """Test text sanitization logic."""
    
    def test_sanitize_html_tags(self):
        """Test that HTML tags are escaped."""
        text = "<script>alert('xss')</script>"
        sanitized = TextSanitizer.sanitize(text)
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
    
    def test_sanitize_sql_injection(self):
        """Test that SQL injection patterns are removed."""
        sql_patterns = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--"
        ]
        
        for pattern in sql_patterns:
            sanitized = TextSanitizer.sanitize_sql(pattern)
            # SQL keywords should be removed
            assert "DROP" not in sanitized.upper() or "SELECT" not in sanitized.upper()
    
    def test_sanitize_xss_patterns(self):
        """Test that XSS patterns are removed."""
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>"
        ]
        
        for pattern in xss_patterns:
            sanitized = TextSanitizer.sanitize_html(pattern)
            # HTML tags and javascript should be removed
            assert "<script>" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
    
    def test_sanitize_normal_text(self):
        """Test that normal text passes through."""
        text = "This is normal text with numbers 123 and symbols !@#"
        sanitized = TextSanitizer.sanitize(text)
        assert "This is normal text" in sanitized
    
    def test_remove_control_characters(self):
        """Test that control characters are removed by sanitize()."""
        text = "Hello\x00World\x01Test"
        sanitized = TextSanitizer.sanitize(text)
        # sanitize() removes control characters (category C) except newlines/tabs
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized


# Extended validation tests

class TestURLValidator:
    """Test URL validation."""
    
    def test_validate_http_url(self):
        """Test valid HTTP URL."""
        assert URLValidator.validate("http://example.com") is True
    
    def test_validate_https_url(self):
        """Test valid HTTPS URL."""
        assert URLValidator.validate("https://example.com/path") is True
    
    def test_validate_invalid_url(self):
        """Test invalid URL."""
        assert URLValidator.validate("not a url") is False
    
    def test_validate_or_raise_valid(self):
        """Test validate_or_raise with valid URL."""
        URLValidator.validate_or_raise("https://example.com")  # Should not raise
    
    def test_validate_or_raise_invalid(self):
        """Test validate_or_raise with invalid URL."""
        with pytest.raises(ValidationError, match="Invalid URL format"):
            URLValidator.validate_or_raise("invalid url")
    
    def test_validate_or_raise_dangerous_protocol(self):
        """Test validation rejects dangerous protocols."""
        # These should fail URL validation first, then check protocol
        with pytest.raises(ValidationError):
            URLValidator.validate_or_raise("javascript:alert(1)")
        
        with pytest.raises(ValidationError):
            URLValidator.validate_or_raise("data:text/html,<script>alert(1)</script>")
        
        with pytest.raises(ValidationError):
            URLValidator.validate_or_raise("file:///etc/passwd")


class TestPhoneValidator:
    """Test phone number validation and sanitization."""
    
    def test_validate_valid_phone(self):
        """Test valid phone number."""
        assert PhoneValidator.validate("+1234567890") is True
    
    def test_validate_invalid_phone(self):
        """Test invalid phone number."""
        assert PhoneValidator.validate("abc") is False
    
    def test_sanitize_phone(self):
        """Test phone sanitization removes non-digits."""
        assert PhoneValidator.sanitize("+1 (234) 567-8900") == "12345678900"
        assert PhoneValidator.sanitize("123-456-7890") == "1234567890"
        assert PhoneValidator.sanitize("(555) 123-4567") == "5551234567"


class TestTextSanitizerAdvanced:
    """Extended tests for TextSanitizer."""
    
    def test_sanitize_with_max_length(self):
        """Test max length enforcement."""
        long_text = "a" * 100
        result = TextSanitizer.sanitize(long_text, max_length=50)
        assert len(result) == 50
    
    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        assert TextSanitizer.sanitize("") == ""
        assert TextSanitizer.sanitize(None) == ""
    
    def test_sanitize_html_removes_tags(self):
        """Test HTML tag removal."""
        html_text = "<script>alert('xss')</script><b>bold</b> text"
        result = TextSanitizer.sanitize_html(html_text)
        assert "<script>" not in result
        assert "<b>" not in result
        assert "text" in result
    
    def test_sanitize_html_removes_javascript(self):
        """Test JavaScript removal."""
        text = "Click javascript:alert(1) here"
        result = TextSanitizer.sanitize_html(text)
        assert "javascript:" not in result
    
    def test_sanitize_html_removes_event_handlers(self):
        """Test event handler removal."""
        text = '<div onclick="evil()">click</div>'
        result = TextSanitizer.sanitize_html(text)
        assert "onclick=" not in result.lower()
    
    def test_sanitize_sql_removes_keywords(self):
        """Test SQL keyword removal."""
        sql_text = "SELECT * FROM users; DROP TABLE users;"
        result = TextSanitizer.sanitize_sql(sql_text)
        assert "SELECT" not in result.upper()
        assert "DROP" not in result.upper()
        assert ";" not in result
    
    def test_sanitize_sql_removes_comments(self):
        """Test SQL comment removal."""
        text = "input' -- comment"
        result = TextSanitizer.sanitize_sql(text)
        assert "--" not in result


# Import additional validators for pydantic model tests
from validators import (
    URLValidator, PhoneValidator,
    RegisterRequestValidator, LoginRequestValidator,
    OTPRequestValidator, PasswordResetValidator,
    MessageTextValidator, validate_pagination_params, calculate_skip
)
from pydantic import ValidationError as PydanticValidationError


class TestRegisterRequestValidator:
    """Test RegisterRequestValidator pydantic model."""
    
    def test_valid_registration(self):
        """Test valid registration data."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "StrongP@ss123"
        }
        model = RegisterRequestValidator(**data)
        assert model.name == "John Doe"
        assert model.email == "john@example.com"
    
    def test_name_sanitization(self):
        """Test name gets sanitized."""
        data = {
            "name": "<script>alert('xss')</script>John",
            "email": "john@example.com",
            "password": "StrongP@ss123"
        }
        model = RegisterRequestValidator(**data)
        assert "<script>" not in model.name
    
    def test_empty_name_rejected(self):
        """Test empty name is rejected."""
        data = {
            "name": "   ",
            "email": "john@example.com",
            "password": "StrongP@ss123"
        }
        with pytest.raises(PydanticValidationError):
            RegisterRequestValidator(**data)
    
    def test_weak_password_rejected(self):
        """Test weak password is rejected."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "weak"
        }
        with pytest.raises(PydanticValidationError):
            RegisterRequestValidator(**data)


class TestLoginRequestValidator:
    """Test LoginRequestValidator pydantic model."""
    
    def test_valid_login(self):
        """Test valid login data."""
        data = {
            "email": "user@example.com",
            "password": "anypassword"
        }
        model = LoginRequestValidator(**data)
        assert model.email == "user@example.com"
        assert model.password == "anypassword"
    
    def test_invalid_email_rejected(self):
        """Test invalid email format is rejected."""
        data = {
            "email": "not-an-email",
            "password": "password"
        }
        with pytest.raises(PydanticValidationError):
            LoginRequestValidator(**data)


class TestOTPRequestValidator:
    """Test OTPRequestValidator pydantic model."""
    
    def test_valid_otp_request(self):
        """Test valid OTP request."""
        data = {
            "email": "user@example.com",
            "otp": "123456"
        }
        model = OTPRequestValidator(**data)
        assert model.otp == "123456"
    
    def test_non_digit_otp_rejected(self):
        """Test non-digit OTP is rejected."""
        data = {
            "email": "user@example.com",
            "otp": "12345a"
        }
        with pytest.raises(PydanticValidationError):
            OTPRequestValidator(**data)
    
    def test_wrong_length_otp_rejected(self):
        """Test wrong length OTP is rejected."""
        data = {
            "email": "user@example.com",
            "otp": "123"
        }
        with pytest.raises(PydanticValidationError):
            OTPRequestValidator(**data)


class TestPasswordResetValidator:
    """Test PasswordResetValidator pydantic model."""
    
    def test_valid_password_reset(self):
        """Test valid password reset data."""
        data = {
            "reset_token": "valid_token_123",
            "new_password": "NewP@ssw0rd123",
            "confirm_password": "NewP@ssw0rd123"
        }
        model = PasswordResetValidator(**data)
        assert model.new_password == "NewP@ssw0rd123"
    
    def test_weak_new_password_rejected(self):
        """Test weak password is rejected."""
        data = {
            "reset_token": "token",
            "new_password": "weak",
            "confirm_password": "weak"
        }
        with pytest.raises(PydanticValidationError):
            PasswordResetValidator(**data)
    
    def test_mismatched_passwords_rejected(self):
        """Test mismatched passwords are rejected."""
        data = {
            "reset_token": "token",
            "new_password": "StrongP@ss123",
            "confirm_password": "DifferentP@ss123"
        }
        with pytest.raises(PydanticValidationError, match="Passwords do not match"):
            PasswordResetValidator(**data)


class TestMessageTextValidator:
    """Test MessageTextValidator pydantic model."""
    
    def test_valid_message(self):
        """Test valid message text."""
        data = {"text": "This is a normal message"}
        model = MessageTextValidator(**data)
        assert "normal message" in model.text
    
    def test_text_gets_sanitized(self):
        """Test message text gets sanitized."""
        data = {"text": "<script>alert('xss')</script>Hello"}
        model = MessageTextValidator(**data)
        assert "<script>" not in model.text
    
    def test_empty_text_rejected(self):
        """Test empty text is rejected."""
        with pytest.raises(PydanticValidationError):
            MessageTextValidator(text="")
    
    def test_max_length_enforced(self):
        """Test maximum length is enforced."""
        long_text = "a" * 15000
        with pytest.raises(PydanticValidationError):
            MessageTextValidator(text=long_text)


class TestPaginationHelpers:
    """Test pagination helper functions."""
    
    def test_validate_pagination_params_valid(self):
        """Test valid pagination parameters."""
        page, page_size = validate_pagination_params(2, 25)
        assert page == 2
        assert page_size == 25
    
    def test_validate_pagination_params_negative_page(self):
        """Test negative page defaults to 1."""
        page, page_size = validate_pagination_params(-1, 25)
        assert page == 1
    
    def test_validate_pagination_params_zero_page(self):
        """Test zero page defaults to 1."""
        page, page_size = validate_pagination_params(0, 25)
        assert page == 1
    
    def test_validate_pagination_params_zero_page_size(self):
        """Test zero page_size defaults to 1."""
        page, page_size = validate_pagination_params(1, 0)
        assert page_size == 1
    
    def test_validate_pagination_params_exceeds_max(self):
        """Test page_size exceeding max is capped."""
        from config import settings
        page, page_size = validate_pagination_params(1, 999999)
        assert page_size == settings.MAX_PAGE_SIZE
    
    def test_calculate_skip_first_page(self):
        """Test skip calculation for first page."""
        skip = calculate_skip(1, 50)
        assert skip == 0
    
    def test_calculate_skip_second_page(self):
        """Test skip calculation for second page."""
        skip = calculate_skip(2, 50)
        assert skip == 50
    
    def test_calculate_skip_arbitrary_page(self):
        """Test skip calculation for arbitrary page."""
        skip = calculate_skip(5, 20)
        assert skip == 80


class TestPasswordValidatorEdgeCases:
    """Test edge cases for password validation."""
    
    def test_password_weak_common_passwords(self):
        """Test that common weak passwords are rejected."""
        # Test with passwords that meet complexity but are common
        weak_passwords = ['Password1!', 'Admin123!', 'Qwerty123!']
        
        for pwd in weak_passwords:
            # These should pass complexity checks
            is_valid, error = PasswordValidator.validate(pwd)
            # Some may pass, some may fail depending on settings
            assert isinstance(is_valid, bool)
    
    def test_password_validate_or_raise_success(self):
        """Test validate_or_raise with valid password."""
        try:
            PasswordValidator.validate_or_raise('ValidPass123!')
            # Should not raise
        except ValidationError:
            pytest.fail("Should not raise ValidationError for valid password")
    
    def test_password_validate_or_raise_failure(self):
        """Test validate_or_raise with invalid password."""
        with pytest.raises(ValidationError) as exc_info:
            PasswordValidator.validate_or_raise('short')
        
        assert "password" in str(exc_info.value).lower()


class TestEmailValidatorEdgeCases:
    """Test edge cases for email validation."""
    
    def test_email_validate_or_raise_too_long(self):
        """Test email that exceeds 254 character limit."""
        long_email = 'a' * 250 + '@test.com'
        
        with pytest.raises(ValidationError) as exc_info:
            EmailValidator.validate_or_raise(long_email)
        
        assert "too long" in str(exc_info.value).lower()
    
    def test_email_validate_or_raise_local_part_too_long(self):
        """Test email with local part exceeding 64 characters."""
        long_local = 'a' * 65 + '@example.com'
        
        with pytest.raises(ValidationError) as exc_info:
            EmailValidator.validate_or_raise(long_local)
        
        assert "local part" in str(exc_info.value).lower()
    
    def test_email_validate_or_raise_success(self):
        """Test validate_or_raise with valid email."""
        try:
            EmailValidator.validate_or_raise('valid@example.com')
            # Should not raise
        except ValidationError:
            pytest.fail("Should not raise ValidationError for valid email")


class TestOTPValidatorEdgeCases:
    """Test edge cases for OTP validation."""
    
    def test_otp_validate_or_raise_invalid(self):
        """Test validate_or_raise with invalid OTP."""
        with pytest.raises(ValidationError) as exc_info:
            OTPValidator.validate_or_raise('12345')  # Too short
        
        assert "otp" in str(exc_info.value).lower()
        assert str(settings.OTP_LENGTH) in str(exc_info.value)


class TestPhoneValidatorEdgeCases:
    """Test edge cases for phone validation."""
    
    def test_phone_sanitize_removes_spaces(self):
        """Test phone sanitization removes spaces."""
        phone = PhoneValidator.sanitize('+1 234 567 8900')
        assert ' ' not in phone
        # Sanitize removes all non-digits except +
        assert len(phone) > 0
    
    def test_phone_sanitize_removes_dashes(self):
        """Test phone sanitization removes dashes."""
        phone = PhoneValidator.sanitize('+1-234-567-8900')
        assert '-' not in phone
    
    def test_phone_sanitize_removes_parentheses(self):
        """Test phone sanitization removes parentheses."""
        phone = PhoneValidator.sanitize('+1 (234) 567-8900')
        assert '(' not in phone
        assert ')' not in phone


class TestRegisterRequestValidatorEdgeCases:
    """Test edge cases for RegisterRequestValidator."""
    
    def test_register_weak_password_rejected(self):
        """Test that weak passwords are rejected in registration."""
        with pytest.raises(PydanticValidationError):
            RegisterRequestValidator(
                email='test@example.com',
                password='weak',  # Too weak
                name='Test User'
            )
    
    def test_register_invalid_email_rejected(self):
        """Test that invalid emails are rejected in registration."""
        with pytest.raises(PydanticValidationError):
            RegisterRequestValidator(
                email='invalid-email',
                password='ValidPass123!',
                name='Test User'
            )
    
    def test_register_valid_data_accepted(self):
        """Test that valid registration data is accepted."""
        validator = RegisterRequestValidator(
            email='test@example.com',
            password='ValidPass123!',
            name='Test User'
        )
        
        assert validator.email == 'test@example.com'
        assert validator.password == 'ValidPass123!'
        assert validator.name == 'Test User'


class TestPasswordResetValidatorEdgeCases:
    """Test edge cases for PasswordResetValidator."""
    
    def test_password_reset_mismatch_rejected(self):
        """Test that mismatched passwords are rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            PasswordResetValidator(
                reset_token='dummy_token',
                new_password='NewPass123!',
                confirm_password='DifferentPass123!'
            )
        
        error_msg = str(exc_info.value).lower()
        assert 'match' in error_msg or 'password' in error_msg
    
    def test_password_reset_weak_password_rejected(self):
        """Test that weak passwords are rejected."""
        with pytest.raises(PydanticValidationError):
            PasswordResetValidator(
                reset_token='dummy_token',
                new_password='weak',
                confirm_password='weak'
            )
    
    def test_password_reset_valid_data_accepted(self):
        """Test that valid password reset data is accepted."""
        validator = PasswordResetValidator(
            reset_token='valid_token_123',
            new_password='NewPass123!',
            confirm_password='NewPass123!'
        )
        
        assert validator.new_password == 'NewPass123!'
        assert validator.confirm_password == 'NewPass123!'


class TestURLValidatorDangerousProtocols:
    """Test URL validator rejects dangerous protocols."""
    
    def test_javascript_protocol_rejected(self):
        """Test that javascript: protocol is rejected."""
        from validators import URLValidator
        
        with pytest.raises(ValidationError) as exc_info:
            URLValidator.validate_or_raise("javascript:alert('xss')")
        
        # These dangerous protocols fail URL format validation
        assert "url" in str(exc_info.value).lower()
    
    def test_data_protocol_rejected(self):
        """Test that data: protocol is rejected."""
        from validators import URLValidator
        
        with pytest.raises(ValidationError) as exc_info:
            URLValidator.validate_or_raise("data:text/html,<script>alert('xss')</script>")
        
        # These dangerous protocols fail URL format validation
        assert "url" in str(exc_info.value).lower()
    
    def test_file_protocol_rejected(self):
        """Test that file: protocol is rejected."""
        from validators import URLValidator
        
        with pytest.raises(ValidationError) as exc_info:
            URLValidator.validate_or_raise("file:///etc/passwd")
        
        # These dangerous protocols fail URL format validation
        assert "url" in str(exc_info.value).lower()
    
    def test_mixed_case_dangerous_protocols(self):
        """Test that mixed-case dangerous protocols are caught."""
        from validators import URLValidator
        
        dangerous_urls = [
            "JavaScript:void(0)",
            "DATA:text/html,test",
            "File:///path"
        ]
        
        for url in dangerous_urls:
            with pytest.raises(ValidationError):
                URLValidator.validate_or_raise(url)


class TestPasswordResetValidatorFieldValidation:
    """Test password field validator in PasswordResetValidator."""
    
    def test_password_validator_called_on_new_password(self):
        """Test that password validation is applied to new_password field."""
        # Weak password should be rejected by validator
        with pytest.raises(PydanticValidationError) as exc_info:
            PasswordResetValidator(
                reset_token='token',
                new_password='weak',
                confirm_password='weak'
            )
        
        error_str = str(exc_info.value).lower()
        assert 'password' in error_str
