"""
Input validation and sanitization utilities.
"""
import re
import html
import unicodedata
from typing import Optional, List, Tuple
from pydantic import BaseModel, EmailStr, validator, Field

from config import settings, ValidationPatterns
from errors import ValidationError


class PasswordValidator:
    """Validator for password strength."""
    
    @staticmethod
    def validate(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[@$!%*?&#^()_+=\-\[\]{}|\\:;"\'<>,.\/]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty', 'admin', 'letmein']
        if password.lower() in weak_passwords:
            return False, "Password is too common. Please choose a stronger password"
        
        return True, None
    
    @staticmethod
    def validate_or_raise(password: str):
        """Validate password or raise ValidationError."""
        is_valid, error_message = PasswordValidator.validate(password)
        if not is_valid:
            raise ValidationError(error_message)


class EmailValidator:
    """Validator for email addresses."""
    
    @staticmethod
    def validate(email: str) -> bool:
        """Check if email format is valid."""
        pattern = re.compile(ValidationPatterns.EMAIL_PATTERN)
        return bool(pattern.match(email))
    
    @staticmethod
    def validate_or_raise(email: str):
        """Validate email or raise ValidationError."""
        if not EmailValidator.validate(email):
            raise ValidationError("Invalid email format")
        
        # Additional checks
        if len(email) > 254:
            raise ValidationError("Email address is too long")
        
        local, domain = email.rsplit('@', 1)
        if len(local) > 64:
            raise ValidationError("Email local part is too long")


class TextSanitizer:
    """Sanitizer for text input to prevent XSS and injection attacks."""
    
    @staticmethod
    def sanitize(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input by removing dangerous characters.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
        
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # Trim whitespace
        text = text.strip()
        
        # Enforce max length
        if max_length and len(text) > max_length:
            text = text[:max_length]
        
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        # Remove control characters except newlines and tabs
        text = ''.join(
            char for char in text
            if unicodedata.category(char)[0] != 'C' or char in '\n\t'
        )
        
        return text
    
    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove all HTML tags from text."""
        # Remove HTML tags
        clean = re.sub(r'<[^>]*>', '', text)
        # Remove JavaScript
        clean = re.sub(r'javascript:', '', clean, flags=re.IGNORECASE)
        # Remove event handlers
        clean = re.sub(r'on\w+\s*=', '', clean, flags=re.IGNORECASE)
        return clean
    
    @staticmethod
    def sanitize_sql(text: str) -> str:
        """Remove SQL injection patterns."""
        # Remove SQL keywords
        dangerous_patterns = [
            r'\bSELECT\b', r'\bDROP\b', r'\bDELETE\b',
            r'\bINSERT\b', r'\bUPDATE\b', r'\bUNION\b',
            r'--', r'/\*', r'\*/', r';'
        ]
        
        clean = text
        for pattern in dangerous_patterns:
            clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)
        
        return clean


class URLValidator:
    """Validator for URLs."""
    
    @staticmethod
    def validate(url: str) -> bool:
        """Check if URL format is valid."""
        pattern = re.compile(ValidationPatterns.URL_PATTERN)
        return bool(pattern.match(url))
    
    @staticmethod
    def validate_or_raise(url: str):
        """Validate URL or raise ValidationError."""
        if not URLValidator.validate(url):
            raise ValidationError("Invalid URL format")
        
        # Check for dangerous protocols
        if url.lower().startswith(('javascript:', 'data:', 'file:')):
            raise ValidationError("Unsafe URL protocol")


class OTPValidator:
    """Validator for OTP codes."""
    
    @staticmethod
    def validate(otp: str) -> bool:
        """Check if OTP format is valid."""
        if not otp:
            return False
        
        # Must be digits only
        if not otp.isdigit():
            return False
        
        # Must match configured length
        if len(otp) != settings.OTP_LENGTH:
            return False
        
        return True
    
    @staticmethod
    def validate_or_raise(otp: str):
        """Validate OTP or raise ValidationError."""
        if not OTPValidator.validate(otp):
            raise ValidationError(
                f"Invalid OTP format. Must be {settings.OTP_LENGTH} digits"
            )


class PhoneValidator:
    """Validator for phone numbers."""
    
    @staticmethod
    def validate(phone: str) -> bool:
        """Check if phone number format is valid."""
        pattern = re.compile(ValidationPatterns.PHONE_PATTERN)
        return bool(pattern.match(phone))
    
    @staticmethod
    def sanitize(phone: str) -> str:
        """Remove non-digit characters from phone number."""
        return re.sub(r'\D', '', phone)


# Pydantic models with built-in validation

class RegisterRequestValidator(BaseModel):
    """Validated model for user registration."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)
    
    @validator('name')
    def validate_name(cls, v):
        """Validate and sanitize name."""
        sanitized = TextSanitizer.sanitize(v, max_length=100)
        if not sanitized:
            raise ValueError("Name cannot be empty")
        return sanitized
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        is_valid, error_message = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error_message)
        return v


class LoginRequestValidator(BaseModel):
    """Validated model for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class OTPRequestValidator(BaseModel):
    """Validated model for OTP operations."""
    email: EmailStr
    otp: str = Field(..., min_length=settings.OTP_LENGTH, max_length=settings.OTP_LENGTH)
    
    @validator('otp')
    def validate_otp(cls, v):
        """Validate OTP format."""
        if not v.isdigit():
            raise ValueError("OTP must contain only digits")
        return v


class PasswordResetValidator(BaseModel):
    """Validated model for password reset."""
    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)
    confirm_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)
    
    @validator('new_password')
    def validate_password(cls, v):
        """Validate password strength."""
        is_valid, error_message = PasswordValidator.validate(v)
        if not is_valid:
            raise ValueError(error_message)
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Ensure passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError("Passwords do not match")
        return v


class MessageTextValidator(BaseModel):
    """Validated model for message text analysis."""
    text: str = Field(..., min_length=1, max_length=10000)
    
    @validator('text')
    def validate_text(cls, v):
        """Sanitize text input."""
        return TextSanitizer.sanitize(v, max_length=10000)


def validate_pagination_params(page: int = 1, page_size: int = 50) -> Tuple[int, int]:
    """
    Validate and sanitize pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Tuple of (validated_page, validated_page_size)
    """
    # Ensure positive values
    page = max(1, page)
    page_size = max(1, min(page_size, settings.MAX_PAGE_SIZE))
    
    return page, page_size


def calculate_skip(page: int, page_size: int) -> int:
    """
    Calculate skip value for pagination.
    
    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Number of items to skip
    """
    return (page - 1) * page_size
