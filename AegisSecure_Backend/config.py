"""
Centralized configuration management for AegisSecure Backend.
All environment variables and constants are defined here.
"""
import os
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration."""

    APP_NAME: str = "AegisSecure Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_HOURS", "12"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    RESET_JWT_TTL_MINUTES: int = int(os.getenv("RESET_JWT_TTL_MINUTES", "15"))

    MONGO_URI: str = os.getenv("MONGO_URI", "")
    DB_NAME: str = os.getenv("DB_NAME", "aegis_secure")

    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
    REFRESH_TOKEN: str = os.getenv("REFRESH_TOKEN", "")

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")

    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
    OTP_LENGTH: int = 6
    OTP_MAX_ATTEMPTS: int = 5

    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    RATE_LIMIT_LOGIN_PER_HOUR: int = int(os.getenv("RATE_LIMIT_LOGIN_PER_HOUR", "5"))

    CYBER_MODEL_URL: str = os.getenv("CYBER_MODEL_URL", "https://cybersecure-backend-api.onrender.com/predict")
    API_TIMEOUT_SECONDS: int = int(os.getenv("API_TIMEOUT_SECONDS", "15"))

    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", None)

    WS_HEARTBEAT_INTERVAL: int = int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
    WS_MAX_CONNECTIONS: int = int(os.getenv("WS_MAX_CONNECTIONS", "1000"))

    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    
    @classmethod
    def validate(cls) -> List[str]:
        """
        Validate that all required environment variables are set.
        Returns list of missing/invalid configurations.
        """
        errors = []
        
        if not cls.JWT_SECRET or len(cls.JWT_SECRET) < 32:
            errors.append("JWT_SECRET must be set and at least 32 characters long")
        
        if not cls.MONGO_URI:
            errors.append("MONGO_URI must be set")
        
        if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
            errors.append("Google OAuth credentials (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) must be set")
        
        if not cls.GOOGLE_REDIRECT_URI:
            errors.append("GOOGLE_REDIRECT_URI must be set")
        
        if not cls.SMTP_EMAIL:
            errors.append("SMTP_EMAIL must be set for email functionality")
        
        return errors
    
    @classmethod
    def print_config_summary(cls):
        """Print non-sensitive configuration for debugging."""
        print("=" * 60)
        print(f"🔧 {cls.APP_NAME} v{cls.APP_VERSION}")
        print("=" * 60)
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"JWT Algorithm: {cls.JWT_ALGORITHM}")
        print(f"JWT Access Token Expiry: {cls.JWT_ACCESS_TOKEN_EXPIRE_HOURS}h")
        print(f"OTP Expiry: {cls.OTP_EXPIRE_MINUTES} minutes")
        print(f"Rate Limiting: {cls.RATE_LIMIT_ENABLED}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print(f"CORS Origins: {cls.CORS_ORIGINS}")
        print("=" * 60)

settings = Settings()

class StatusMessages:
    """Standardized status messages for API responses."""

    SUCCESS = "Operation completed successfully"
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"

    LOGIN_SUCCESS = "Login successful"
    LOGOUT_SUCCESS = "Logout successful"
    REGISTRATION_SUCCESS = "User registered successfully"
    OTP_SENT = "OTP sent to your email"
    OTP_VERIFIED = "OTP verified successfully"
    PASSWORD_RESET_SUCCESS = "Password reset successfully"

    INVALID_CREDENTIALS = "Invalid email or password"
    USER_NOT_FOUND = "User not found"
    EMAIL_ALREADY_EXISTS = "Email already registered"
    INVALID_TOKEN = "Invalid or expired token"
    UNAUTHORIZED = "Unauthorized access"
    ACCOUNT_NOT_VERIFIED = "Please verify your account first"

    INVALID_INPUT = "Invalid input data"
    MISSING_FIELDS = "Required fields are missing"
    INVALID_EMAIL = "Invalid email format"
    WEAK_PASSWORD = "Password does not meet security requirements"

    INVALID_OTP = "Invalid or expired OTP"
    OTP_EXPIRED = "OTP has expired"
    MAX_OTP_ATTEMPTS = "Maximum OTP attempts exceeded"

    INTERNAL_ERROR = "Internal server error"
    SERVICE_UNAVAILABLE = "Service temporarily unavailable"
    DATABASE_ERROR = "Database operation failed"
    EXTERNAL_API_ERROR = "External API request failed"

    RESOURCE_NOT_FOUND = "Resource not found"
    DUPLICATE_RESOURCE = "Resource already exists"

    RATE_LIMIT_EXCEEDED = "Too many requests. Please try again later"

class ValidationPatterns:
    """Regex patterns for input validation."""
    
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?1?\d{9,15}$'
    URL_PATTERN = r'^https?://[^\s/$.?#].[^\s]*$'

    PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

class SecurityHeaders:
    """Security headers to be added to responses."""
    
    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
