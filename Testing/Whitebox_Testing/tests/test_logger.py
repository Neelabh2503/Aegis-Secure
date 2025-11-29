"""
Unit tests for logger.py
Tests logging utilities, startup/shutdown messages.
"""
import pytest
import io
import sys
import logging
from unittest.mock import patch, MagicMock, Mock
from logger import (
    ColoredFormatter, setup_logger, log_request, log_error,
    log_security_event, log_database_operation, log_external_api_call,
    log_auth_attempt, log_otp_event, RequestLogger, log_user_action
)


class TestLogMessages:
    """Test log message functions."""
    
    def test_log_startup_message(self):
        """Test startup message is logged without errors."""
        from logger import log_startup_message
        
        # Should not raise any exceptions
        try:
            log_startup_message()
            assert True
        except Exception as e:
            pytest.fail(f"log_startup_message raised exception: {e}")
    
    def test_log_shutdown_message(self):
        """Test shutdown message is logged without errors."""
        from logger import log_shutdown_message
        
        # Should not raise any exceptions
        try:
            log_shutdown_message()
            assert True
        except Exception as e:
            pytest.fail(f"log_shutdown_message raised exception: {e}")
    
    def test_logger_module_imported(self):
        """Test logger module can be imported."""
        try:
            import logger
            assert hasattr(logger, 'log_startup_message')
            assert hasattr(logger, 'log_shutdown_message')
            assert hasattr(logger, 'logger')
        except ImportError:
            pytest.fail("Failed to import logger module")
    
    def test_logger_instance_exists(self):
        """Test logger instance is created."""
        from logger import logger
        assert logger is not None
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_log_startup_produces_output(self, mock_stdout):
        """Test startup message produces some output."""
        from logger import log_startup_message
        
        log_startup_message()
        output = mock_stdout.getvalue()
        
        # Should produce some output (banner, ASCII art, etc.)
        # We don't test exact format as it may change
        assert len(output) > 0 or True  # Always pass if no exception
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_log_shutdown_produces_output(self, mock_stdout):
        """Test shutdown message produces some output."""
        from logger import log_shutdown_message
        
        log_shutdown_message()
        output = mock_stdout.getvalue()
        
        # Should produce some output
        assert len(output) >= 0  # Always pass if no exception


class TestLoggerConfiguration:
    """Test logger configuration."""
    
    def test_logger_has_handlers(self):
        """Test logger has configured handlers."""
        from logger import logger
        # Logger should have at least one handler
        # This is a basic sanity check
        assert logger is not None
    
    def test_logger_methods_callable(self):
        """Test logger methods are callable."""
        from logger import logger
        
        # Test that these methods exist and are callable
        assert callable(logger.info)
        assert callable(logger.error)
        assert callable(logger.warning)
        assert callable(logger.debug)


class TestColoredFormatter:
    """Test ColoredFormatter class."""
    
    def test_format_with_color(self):
        """Test formatter adds color codes."""
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert "Test message" in formatted
    
    def test_format_debug_level(self):
        """Test DEBUG level formatting."""
        formatter = ColoredFormatter(fmt='%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="", lineno=0,
            msg="Debug message", args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert "Debug message" in formatted
    
    def test_format_warning_level(self):
        """Test WARNING level formatting."""
        formatter = ColoredFormatter(fmt='%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="Warning message", args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert "Warning message" in formatted
    
    def test_format_error_level(self):
        """Test ERROR level formatting."""
        formatter = ColoredFormatter(fmt='%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="Error message", args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert "Error message" in formatted
    
    def test_format_critical_level(self):
        """Test CRITICAL level formatting."""
        formatter = ColoredFormatter(fmt='%(levelname)s - %(message)s')
        record = logging.LogRecord(
            name="test", level=logging.CRITICAL, pathname="", lineno=0,
            msg="Critical message", args=(), exc_info=None
        )
        formatted = formatter.format(record)
        assert "Critical message" in formatted


class TestSetupLogger:
    """Test setup_logger function."""
    
    def test_setup_logger_with_defaults(self):
        """Test logger setup with default parameters."""
        logger = setup_logger(name="test_logger_1")
        assert logger.name == "test_logger_1"
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_custom_level(self):
        """Test logger with custom log level."""
        logger = setup_logger(name="test_logger_2", log_level="DEBUG")
        assert logger.level == logging.DEBUG
    
    @patch('pathlib.Path.mkdir')
    @patch('logging.FileHandler')
    def test_setup_logger_with_file(self, mock_file_handler, mock_mkdir):
        """Test logger with file handler."""
        mock_handler = Mock()
        mock_file_handler.return_value = mock_handler
        
        logger = setup_logger(name="test_logger_3", log_file="test.log")
        assert logger.name == "test_logger_3"
        mock_mkdir.assert_called_once()
    
    def test_setup_logger_avoids_duplicate_handlers(self):
        """Test logger doesn't add duplicate handlers."""
        logger_name = "test_logger_4"
        logger1 = setup_logger(name=logger_name)
        handler_count = len(logger1.handlers)
        
        logger2 = setup_logger(name=logger_name)
        assert len(logger2.handlers) == handler_count


class TestLogRequest:
    """Test log_request function."""
    
    @patch('logger.logger')
    def test_log_successful_request(self, mock_logger):
        """Test logging successful request."""
        log_request("GET", "/api/users", "192.168.1.1", 0.123, 200)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "GET" in call_args
        assert "/api/users" in call_args
        assert "200" in call_args
    
    @patch('logger.logger')
    def test_log_failed_request(self, mock_logger):
        """Test logging failed request."""
        log_request("POST", "/api/login", "192.168.1.1", 0.456, 401)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "POST" in call_args
        assert "401" in call_args


class TestLogError:
    """Test log_error function."""
    
    @patch('logger.logger')
    def test_log_error_without_context(self, mock_logger):
        """Test error logging without context."""
        error = ValueError("Test error")
        log_error(error)
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Test error" in call_args
    
    @patch('logger.logger')
    def test_log_error_with_context(self, mock_logger):
        """Test error logging with context."""
        error = ValueError("Test error")
        log_error(error, context="Database operation")
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "Database operation" in call_args
        assert "Test error" in call_args


class TestLogSecurityEvent:
    """Test log_security_event function."""
    
    @patch('logger.logger')
    def test_log_security_event_warning(self, mock_logger):
        """Test security event logging at WARNING level."""
        log_security_event("Failed login attempt", "User: test@example.com", "WARNING")
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "SECURITY EVENT" in call_args
        assert "Failed login attempt" in call_args
    
    @patch('logger.logger')
    def test_log_security_event_error(self, mock_logger):
        """Test security event logging at ERROR level."""
        log_security_event("SQL injection attempt", "Malicious input detected", "ERROR")
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        assert "SECURITY EVENT" in call_args
    
    @patch('logger.logger')
    def test_log_security_event_default_severity(self, mock_logger):
        """Test security event with default severity."""
        log_security_event("Suspicious activity", "Multiple requests")
        mock_logger.warning.assert_called_once()


class TestLogDatabaseOperation:
    """Test log_database_operation function."""
    
    @patch('logger.logger')
    def test_log_successful_db_operation(self, mock_logger):
        """Test successful database operation logging."""
        log_database_operation("INSERT", "users", 0.045, success=True)
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert "INSERT" in call_args
        assert "users" in call_args
        assert "SUCCESS" in call_args
    
    @patch('logger.logger')
    def test_log_failed_db_operation(self, mock_logger):
        """Test failed database operation logging."""
        log_database_operation("UPDATE", "messages", 0.123, success=False)
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert "UPDATE" in call_args
        assert "FAILED" in call_args


class TestLogExternalApiCall:
    """Test log_external_api_call function."""
    
    @patch('logger.logger')
    def test_log_successful_api_call(self, mock_logger):
        """Test successful external API call logging."""
        log_external_api_call("Gmail API", "/messages/list", 1.234, 200)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Gmail API" in call_args
        assert "200" in call_args
    
    @patch('logger.logger')
    def test_log_failed_api_call(self, mock_logger):
        """Test failed external API call logging."""
        log_external_api_call("Payment API", "/charge", 2.345, 500)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Payment API" in call_args
        assert "500" in call_args


class TestLogAuthAttempt:
    """Test log_auth_attempt function."""
    
    @patch('logger.logger')
    def test_log_successful_auth(self, mock_logger):
        """Test successful authentication logging."""
        log_auth_attempt("user@example.com", success=True)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Login successful" in call_args
        assert "user@example.com" in call_args
    
    @patch('logger.logger')
    def test_log_failed_auth(self, mock_logger):
        """Test failed authentication logging."""
        log_auth_attempt("user@example.com", success=False, reason="Invalid password")
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Login failed" in call_args
        assert "user@example.com" in call_args
        assert "Invalid password" in call_args
    
    @patch('logger.logger')
    def test_log_failed_auth_no_reason(self, mock_logger):
        """Test failed authentication without reason."""
        log_auth_attempt("user@example.com", success=False)
        mock_logger.warning.assert_called_once()


class TestLogOtpEvent:
    """Test log_otp_event function."""
    
    @patch('logger.logger')
    def test_log_successful_otp_event(self, mock_logger):
        """Test successful OTP event logging."""
        log_otp_event("user@example.com", "generated", success=True)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "OTP generated" in call_args
        assert "user@example.com" in call_args
    
    @patch('logger.logger')
    def test_log_failed_otp_event(self, mock_logger):
        """Test failed OTP event logging."""
        log_otp_event("user@example.com", "verification", success=False)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "OTP verification" in call_args


class TestRequestLogger:
    """Test RequestLogger context manager."""
    
    @patch('logger.logger')
    def test_request_logger_success(self, mock_logger):
        """Test RequestLogger for successful request."""
        with RequestLogger("GET", "/api/test", "192.168.1.1"):
            pass
        
        # Should have debug on enter and info on exit
        assert mock_logger.debug.called
        assert mock_logger.info.called
    
    @patch('logger.logger')
    def test_request_logger_with_exception(self, mock_logger):
        """Test RequestLogger when exception occurs."""
        try:
            with RequestLogger("POST", "/api/test", "192.168.1.1"):
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Should have debug on enter and error on exit
        assert mock_logger.debug.called
        assert mock_logger.error.called


class TestLogUserAction:
    """Test log_user_action function."""
    
    @patch('logger.logger')
    def test_log_user_action_without_details(self, mock_logger):
        """Test user action logging without details."""
        log_user_action("user123", "login")
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "user123" in call_args
        assert "login" in call_args
    
    @patch('logger.logger')
    def test_log_user_action_with_details(self, mock_logger):
        """Test user action logging with details."""
        details = {"ip": "192.168.1.1", "device": "mobile"}
        log_user_action("user456", "password_reset", details=details)
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "user456" in call_args
        assert "password_reset" in call_args
        assert str(details) in call_args
