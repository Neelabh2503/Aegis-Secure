"""
Tests for Pydantic models
"""
import pytest
from pydantic import ValidationError
from models import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    SendOTPRequest,
    UserResponse,
    VerifyOTPRequest,
    ResetPasswordRequest,
    Spam_request,
    SpamRequest,
    SmsMessage,
    SmsSyncRequest
)


class TestRegisterRequest:
    """Test RegisterRequest model"""
    
    def test_valid_register_request(self):
        """Test valid registration request"""
        req = RegisterRequest(
            name="Test User",
            email="test@example.com",
            password="SecurePass123!"
        )
        assert req.name == "Test User"
        assert req.email == "test@example.com"
        assert req.password == "SecurePass123!"
    
    def test_register_request_missing_fields(self):
        """Test registration request with missing fields"""
        with pytest.raises(ValidationError):
            RegisterRequest(name="Test", email="test@example.com")


class TestLoginRequest:
    """Test LoginRequest model"""
    
    def test_valid_login_request(self):
        """Test valid login request"""
        req = LoginRequest(
            email="test@example.com",
            password="password123"
        )
        assert req.email == "test@example.com"
        assert req.password == "password123"
    
    def test_login_request_missing_password(self):
        """Test login request with missing password"""
        with pytest.raises(ValidationError):
            LoginRequest(email="test@example.com")


class TestLoginResponse:
    """Test LoginResponse model"""
    
    def test_valid_login_response(self):
        """Test valid login response"""
        resp = LoginResponse(token="jwt_token_here", verified=True)
        assert resp.token == "jwt_token_here"
        assert resp.verified is True
    
    def test_login_response_unverified(self):
        """Test login response for unverified user"""
        resp = LoginResponse(token="jwt_token_here", verified=False)
        assert resp.verified is False


class TestSendOTPRequest:
    """Test SendOTPRequest model"""
    
    def test_valid_otp_request(self):
        """Test valid OTP request with email"""
        req = SendOTPRequest(email="test@example.com")
        assert req.email == "test@example.com"
    
    def test_invalid_email_format(self):
        """Test OTP request with invalid email format"""
        with pytest.raises(ValidationError):
            SendOTPRequest(email="not-an-email")


class TestUserResponse:
    """Test UserResponse model"""
    
    def test_valid_user_response(self):
        """Test valid user response"""
        resp = UserResponse(
            name="Test User",
            email="test@example.com",
            user_id="user123"
        )
        assert resp.name == "Test User"
        assert resp.email == "test@example.com"
        assert resp.user_id == "user123"


class TestVerifyOTPRequest:
    """Test VerifyOTPRequest model"""
    
    def test_valid_verify_otp_request(self):
        """Test valid OTP verification request"""
        req = VerifyOTPRequest(email="test@example.com", otp="123456")
        assert req.email == "test@example.com"
        assert req.otp == "123456"
    
    def test_invalid_email_in_verify_otp(self):
        """Test OTP verification with invalid email"""
        with pytest.raises(ValidationError):
            VerifyOTPRequest(email="invalid-email", otp="123456")


class TestResetPasswordRequest:
    """Test ResetPasswordRequest model"""
    
    def test_valid_reset_password_request(self):
        """Test valid password reset request"""
        req = ResetPasswordRequest(
            reset_token="token123",
            new_password="NewPass123!",
            confirm_password="NewPass123!"
        )
        assert req.reset_token == "token123"
        assert req.new_password == "NewPass123!"
        assert req.confirm_password == "NewPass123!"
    
    def test_reset_password_missing_fields(self):
        """Test password reset with missing fields"""
        with pytest.raises(ValidationError):
            ResetPasswordRequest(reset_token="token", new_password="pass")


class TestSpamRequest:
    """Test Spam_request and SpamRequest models"""
    
    def test_valid_spam_request(self):
        """Test valid spam request"""
        req = Spam_request(
            sender="spam@example.com",
            subject="Spam Subject",
            text="Spam message content"
        )
        assert req.sender == "spam@example.com"
        assert req.subject == "Spam Subject"
        assert req.text == "Spam message content"
    
    def test_valid_spam_request_alternate(self):
        """Test valid SpamRequest (alternate model)"""
        req = SpamRequest(
            sender="spam@example.com",
            subject="Spam Subject",
            text="Spam message content"
        )
        assert req.sender == "spam@example.com"
        assert req.subject == "Spam Subject"
        assert req.text == "Spam message content"
    
    def test_spam_request_missing_fields(self):
        """Test spam request with missing fields"""
        with pytest.raises(ValidationError):
            Spam_request(sender="spam@example.com", subject="Test")


class TestSmsMessage:
    """Test SmsMessage model"""
    
    def test_valid_sms_message(self):
        """Test valid SMS message"""
        msg = SmsMessage(
            address="+1234567890",
            body="Test message",
            date_ms=1234567890000,
            type="inbox"
        )
        assert msg.address == "+1234567890"
        assert msg.body == "Test message"
        assert msg.date_ms == 1234567890000
        assert msg.type == "inbox"
    
    def test_sms_message_sent_type(self):
        """Test SMS message with sent type"""
        msg = SmsMessage(
            address="+1234567890",
            body="Sent message",
            date_ms=1234567890000,
            type="sent"
        )
        assert msg.type == "sent"
    
    def test_sms_message_missing_fields(self):
        """Test SMS message with missing fields"""
        with pytest.raises(ValidationError):
            SmsMessage(address="+123", body="Test", date_ms=123)


class TestSmsSyncRequest:
    """Test SmsSyncRequest model"""
    
    def test_valid_sms_sync_request(self):
        """Test valid SMS sync request with multiple messages"""
        messages = [
            SmsMessage(address="+111", body="Msg1", date_ms=1000, type="inbox"),
            SmsMessage(address="+222", body="Msg2", date_ms=2000, type="sent")
        ]
        req = SmsSyncRequest(messages=messages)
        assert len(req.messages) == 2
        assert req.messages[0].address == "+111"
        assert req.messages[1].address == "+222"
    
    def test_sms_sync_request_empty_list(self):
        """Test SMS sync request with empty message list"""
        req = SmsSyncRequest(messages=[])
        assert len(req.messages) == 0
    
    def test_sms_sync_request_single_message(self):
        """Test SMS sync request with single message"""
        messages = [
            SmsMessage(address="+111", body="Single", date_ms=1000, type="inbox")
        ]
        req = SmsSyncRequest(messages=messages)
        assert len(req.messages) == 1


class TestModelValidation:
    """Test model validation edge cases"""
    
    def test_register_request_empty_strings(self):
        """Test registration with empty strings"""
        req = RegisterRequest(name="", email="", password="")
        assert req.name == ""
        assert req.email == ""
    
    def test_login_response_empty_token(self):
        """Test login response with empty token"""
        resp = LoginResponse(token="", verified=False)
        assert resp.token == ""
    
    def test_user_response_special_characters(self):
        """Test user response with special characters in name"""
        resp = UserResponse(
            name="Test User™",
            email="test@example.com",
            user_id="123"
        )
        assert "™" in resp.name
