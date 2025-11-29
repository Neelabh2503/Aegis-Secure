"""
Comprehensive logging configuration for AegisSecure backend.
"""
import logging
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

from config import settings

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):

        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

def setup_logger(
    name: str = "aegis_secure",
    log_level: Optional[str] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure application logger.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    
    Returns:
        Configured logger instance
    """

    logger = logging.getLogger(name)
    logger.setLevel(log_level or settings.LOG_LEVEL)

    if logger.handlers:
        return logger

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file or settings.LOG_FILE:
        file_path = Path(log_file or settings.LOG_FILE)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

def log_request(method: str, path: str, client_ip: str, duration: float, status_code: int):
    """Log API request details."""
    emoji = "✅" if status_code < 400 else "❌"
    logger.info(
        f"{emoji} {method} {path} - IP: {client_ip} - Status: {status_code} - "
        f"Duration: {duration:.3f}s"
    )

def log_error(error: Exception, context: Optional[str] = None):
    """Log error with context."""
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg = f"{context} | {error_msg}"
    logger.error(error_msg, exc_info=True)

def log_security_event(event_type: str, details: str, severity: str = "WARNING"):
    """Log security-related events."""
    log_func = getattr(logger, severity.lower(), logger.warning)
    log_func(f"🔒 SECURITY EVENT: {event_type} | {details}")

def log_database_operation(operation: str, collection: str, duration: float, success: bool = True):
    """Log database operations."""
    status = "✅ SUCCESS" if success else "❌ FAILED"
    logger.debug(
        f"💾 DB {operation} on '{collection}' - {status} - Duration: {duration:.3f}s"
    )

def log_external_api_call(service: str, endpoint: str, duration: float, status_code: int):
    """Log external API calls."""
    emoji = "🔗" if status_code < 400 else "⚠️"
    logger.info(
        f"{emoji} External API: {service} | {endpoint} - "
        f"Status: {status_code} - Duration: {duration:.3f}s"
    )

def log_auth_attempt(email: str, success: bool, reason: Optional[str] = None):
    """Log authentication attempts."""
    if success:
        logger.info(f"🔐 Login successful: {email}")
    else:
        reason_msg = f" | Reason: {reason}" if reason else ""
        logger.warning(f"🔐 Login failed: {email}{reason_msg}")

def log_otp_event(email: str, event: str, success: bool = True):
    """Log OTP-related events."""
    emoji = "✅" if success else "❌"
    logger.info(f"{emoji} OTP {event}: {email}")

class RequestLogger:
    """Context manager for logging request lifecycle."""
    
    def __init__(self, method: str, path: str, client_ip: str):
        self.method = method
        self.path = path
        self.client_ip = client_ip
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.debug(f"🔵 {self.method} {self.path} - Client: {self.client_ip}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.info(
                f"✅ {self.method} {self.path} - "
                f"Duration: {duration:.3f}s"
            )
        else:
            logger.error(
                f"❌ {self.method} {self.path} - "
                f"Error: {exc_val} - Duration: {duration:.3f}s"
            )

def log_user_action(user_id: str, action: str, details: Optional[dict] = None):
    """Log user actions for audit trail."""
    msg = f"👤 User {user_id} | Action: {action}"
    if details:
        msg += f" | Details: {details}"
    logger.info(msg)

def log_websocket_event(event_type: str, connection_count: int):
    """Log WebSocket events."""
    logger.info(f"🔌 WebSocket {event_type} | Active connections: {connection_count}")

def log_startup_message():
    """Log application startup message."""
    logger.info("=" * 60)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    logger.info(f"📝 Log Level: {settings.LOG_LEVEL}")
    logger.info(f"🐛 Debug Mode: {settings.DEBUG}")
    logger.info("=" * 60)

def log_shutdown_message():
    """Log application shutdown message."""
    logger.info("=" * 60)
    logger.info(f"🛑 {settings.APP_NAME} shutting down...")
    logger.info("=" * 60)
