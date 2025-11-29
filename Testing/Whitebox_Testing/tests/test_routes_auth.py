"""
Unit tests for routes/auth.py
Tests authentication, registration, JWT, and password management.
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import jwt as jose_jwt
from fastapi import HTTPException
from .test_helpers import AsyncMock
from routes import auth
from config import settings
from errors import AuthenticationError, ValidationError, TokenError, DuplicateResourceError
from utils.password_utils import pwd_context
from utils.jwt_utils import create_reset_jwt, decode_reset_jwt, JWT_SECRET, JWT_ALGORITHM
import models


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password can be hashed."""
        password = "SecurePass123!"
        hashed = pwd_context.hash(password)
        assert hashed != password
        assert len(hashed) > 20
    
    def test_verify_correct_password(self):
        """Test correct password verification."""
        password = "SecurePass123!"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed)
    
    def test_verify_incorrect_password(self):
        """Test incorrect password rejection."""
        password = "SecurePass123!"
        hashed = pwd_context.hash(password)
        assert not pwd_context.verify("WrongPass456!", hashed)
    
    def test_different_hashes_for_same_password(self):
        """Test salts create different hashes."""
        password = "SecurePass123!"
        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)
        assert hash1 != hash2
        # But both verify correctly
        assert pwd_context.verify(password, hash1)
        assert pwd_context.verify(password, hash2)


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_reset_jwt(self):
        """Test password reset JWT creation."""
        email = "test@example.com"
        token = create_reset_jwt(email)
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_decode_reset_jwt_valid(self):
        """Test decoding valid reset token."""
        email = "test@example.com"
        token = create_reset_jwt(email)
        payload = decode_reset_jwt(token)
        assert payload["sub"] == email
        assert payload["purpose"] == "password_reset"
    
    def test_decode_reset_jwt_expired(self):
        """Test expired token rejection."""
        from fastapi import HTTPException
        exp = datetime.utcnow() - timedelta(minutes=1)
        payload = {"sub": "test@example.com", "purpose": "password_reset", "exp": exp}
        token = jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt(token)
        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()
    
    def test_decode_reset_jwt_wrong_purpose(self):
        """Test token with wrong purpose is rejected."""
        from fastapi import HTTPException
        exp = datetime.utcnow() + timedelta(minutes=10)
        payload = {"sub": "test@example.com", "purpose": "email_verify", "exp": exp}
        token = jose_jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt(token)
        assert exc_info.value.status_code == 401
        assert "purpose" in str(exc_info.value.detail).lower()
    
    def test_decode_reset_jwt_invalid(self):
        """Test invalid token rejection."""
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt("invalid.token.here")
        assert exc_info.value.status_code == 401
    
    def test_reset_jwt_has_expiration(self):
        """Test reset token has expiration field."""
        email = "test@example.com"
        token = create_reset_jwt(email)
        payload = jose_jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Token should have expiration
        assert "exp" in payload
        # Expiration should be in the future
        assert payload["exp"] > datetime.utcnow().timestamp()


class TestRegistrationValidation:
    """Test registration input validation."""
    
    def test_register_request_model_valid(self):
        """Test valid registration request."""
        req = models.RegisterRequest(
            name="John Doe",
            email="john@example.com",
            password="SecurePass123!"
        )
        assert req.name == "John Doe"
        assert req.email == "john@example.com"
        assert req.password == "SecurePass123!"
    
    def test_register_request_missing_fields(self):
        """Test registration with missing fields."""
        with pytest.raises(ValueError):
            models.RegisterRequest(email="test@example.com")
    
    def test_login_request_model(self):
        """Test login request model."""
        req = models.LoginRequest(
            email="user@example.com",
            password="password123"
        )
        assert req.email == "user@example.com"
        assert req.password == "password123"


class TestOTPModels:
    """Test OTP-related models."""
    
    def test_send_otp_request_valid_email(self):
        """Test OTP request with valid email."""
        req = models.SendOTPRequest(email="test@example.com")
        assert req.email == "test@example.com"
    
    def test_send_otp_request_invalid_email(self):
        """Test OTP request with invalid email."""
        with pytest.raises(ValueError):
            models.SendOTPRequest(email="not-an-email")
    
    def test_verify_otp_request(self):
        """Test OTP verification request."""
        req = models.VerifyOTPRequest(
            email="test@example.com",
            otp="123456"
        )
        assert req.email == "test@example.com"
        assert req.otp == "123456"
    
class TestResetPasswordModel:
    """Test password reset request model."""
    
    def test_reset_password_request_valid(self):
        """Test valid password reset request."""
        req = models.ResetPasswordRequest(
            reset_token="token_here",
            new_password="NewPass123!",
            confirm_password="NewPass123!"
        )
        assert req.reset_token == "token_here"
        assert req.new_password == "NewPass123!"
        assert req.confirm_password == "NewPass123!"
    
    def test_reset_password_request_missing_fields(self):
        """Test reset request with missing fields."""
        with pytest.raises(ValueError):
            models.ResetPasswordRequest(reset_token="token")


class TestUserResponse:
    """Test user response model."""
    
    def test_user_response_model(self):
        """Test user response structure."""
        user = models.UserResponse(
            name="Jane Doe",
            email="jane@example.com",
            user_id="user_123"
        )
        assert user.name == "Jane Doe"
        assert user.email == "jane@example.com"
        assert user.user_id == "user_123"


class TestLoginResponse:
    """Test login response model."""
    
    def test_login_response_model(self):
        """Test login response structure."""
        response = models.LoginResponse(
            token="jwt_token_here",
            verified=True
        )
        assert response.token == "jwt_token_here"
        assert response.verified is True
    
    def test_login_response_unverified(self):
        """Test login response for unverified user."""
        response = models.LoginResponse(
            token="jwt_token_here",
            verified=False
        )
        assert response.verified is False


class TestAuthConfiguration:
    """Test authentication configuration."""
    
    def test_jwt_algorithm_configured(self):
        """Test JWT algorithm is set."""
        assert settings.JWT_ALGORITHM == "HS256"
    
    def test_password_requirements_exist(self):
        """Test password requirements are configured."""
        assert settings.PASSWORD_MIN_LENGTH >= 8
        assert settings.PASSWORD_REQUIRE_UPPERCASE
        assert settings.PASSWORD_REQUIRE_LOWERCASE
        assert settings.PASSWORD_REQUIRE_DIGIT
        assert settings.PASSWORD_REQUIRE_SPECIAL
    
    def test_reset_jwt_ttl_configured(self):
        """Test reset token TTL is configured."""
        assert hasattr(settings, 'RESET_JWT_TTL_MINUTES')
        assert settings.RESET_JWT_TTL_MINUTES > 0
        assert settings.RESET_JWT_TTL_MINUTES <= 60


class TestHTTPBearer:
    """Test HTTP Bearer security scheme."""
    
    def test_security_scheme_configured(self):
        """Test security scheme is properly set up."""
        assert auth.security is not None
        assert isinstance(auth.security, auth.HTTPBearer)


class TestRegisterUserOTPPaths:
    """Test register user OTP sending scenarios."""
    
    @pytest.mark.asyncio
    async def test_register_otp_sent_success(self):
        """Test registration with OTP successfully sent."""
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('routes.auth.users_col.insert_one', new_callable=AsyncMock), \
             patch('routes.auth.generate_otp', return_value='123456'), \
             patch('routes.auth.store_otp', new_callable=AsyncMock), \
             patch('routes.auth.send_otp', new_callable=AsyncMock, return_value=True):
            
            response = await auth.register_user(models.RegisterRequest(
                name='Test User',
                email='test@example.com',
                password='SecurePass123!'
            ))
            
            assert 'OTP sent to email' in response['message']
            assert '123456' not in response['message']  # Should not expose OTP
    
    @pytest.mark.asyncio
    async def test_register_otp_dev_mode(self):
        """Test registration in dev mode shows OTP."""
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('routes.auth.users_col.insert_one', new_callable=AsyncMock), \
             patch('routes.auth.generate_otp', return_value='654321'), \
             patch('routes.auth.store_otp', new_callable=AsyncMock), \
             patch('routes.auth.send_otp', new_callable=AsyncMock, return_value=False):
            
            response = await auth.register_user(models.RegisterRequest(
                name='Test User',
                email='test@example.com',
                password='SecurePass123!'
            ))
            
            assert 'dev mode' in response['message'].lower()
            assert '654321' in response['message']


class TestSendOTPPaths:
    """Test send OTP endpoint scenarios."""
    
    @pytest.mark.asyncio
    async def test_send_otp_email_sent(self):
        """Test send OTP with email sent successfully."""
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value={'email': 'test@example.com'}), \
             patch('routes.auth.generate_otp', return_value='111111'), \
             patch('routes.auth.store_otp', new_callable=AsyncMock), \
             patch('routes.auth.send_otp', new_callable=AsyncMock, return_value=True):
            
            response = await auth.send_otp_router(models.SendOTPRequest(email='test@example.com'))
            
            assert 'OTP sent to your email' in response['message']
    
    @pytest.mark.asyncio
    async def test_send_otp_dev_mode(self):
        """Test send OTP in dev mode."""
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value={'email': 'test@example.com'}), \
             patch('routes.auth.generate_otp', return_value='222222'), \
             patch('routes.auth.store_otp', new_callable=AsyncMock), \
             patch('routes.auth.send_otp', new_callable=AsyncMock, return_value=False):
            
            response = await auth.send_otp_router(models.SendOTPRequest(email='test@example.com'))
            
            assert 'dev mode' in response['message'].lower()
            assert '222222' in response['message']


class TestVerifyOTPException:
    """Test verify OTP exception handling."""
    
    @pytest.mark.asyncio
    async def test_verify_otp_catches_exception(self):
        """Test verify OTP handles exceptions properly."""
        with patch('routes.auth.verify_otp_in_db', new_callable=AsyncMock, side_effect=Exception('DB error')), \
             patch('builtins.print'):
            
            from routes.auth import verify_otp
            from models import VerifyOTPRequest
            
            with pytest.raises(Exception) as exc_info:
                await verify_otp(VerifyOTPRequest(email='test@example.com', otp='123456'))
            
            assert 'DB error' in str(exc_info.value)


class TestDecodeJWTErrors:
    """Test JWT decoding error paths."""
    
    def test_decode_expired_token(self):
        """Test decoding expired JWT token."""
        from routes.auth import decode_jwt
        import jwt
        import datetime
        
        # Create expired token
        payload = {
            'email': 'test@example.com',
            'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        }
        expired_token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(expired_token)
        
        assert exc_info.value.status_code == 401
        assert 'expired' in exc_info.value.detail.lower()
    
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token."""
        from routes.auth import decode_jwt
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt('invalid.token.here')
        
        assert exc_info.value.status_code == 401
        assert 'invalid' in exc_info.value.detail.lower()


class TestGetUserInfoEndpoint:
    """Test get user info endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_user_info_user_not_found(self):
        """Test get user info when user doesn't exist."""
        from routes.auth import get_user_info
        from fastapi.security import HTTPAuthorizationCredentials
        import jwt
        import datetime
        
        # Create valid token
        payload = {
            'email': 'nonexistent@example.com',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_user_info(credentials)
            
            assert exc_info.value.status_code == 404


class TestUploadAvatar:
    """Test avatar upload functionality."""
    
    @pytest.mark.asyncio
    async def test_upload_avatar_success(self):
        """Test successful avatar upload."""
        from routes.auth import upload_avatar
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import UploadFile
        from io import BytesIO
        import jwt
        import datetime
        
        payload = {
            'email': 'test@example.com',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        mock_user = {'email': 'test@example.com', 'name': 'Test User'}
        mock_update = AsyncMock(return_value=Mock(modified_count=1))
        
        file_content = b'fake image data'
        file = UploadFile(filename='avatar.jpg', file=BytesIO(file_content))
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with patch('routes.auth.users_col.update_one', new_callable=AsyncMock, return_value=mock_update.return_value):
                credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
                result = await upload_avatar(credentials, file)
                
                assert 'avatar_base64' in result.body.decode()
    
    @pytest.mark.asyncio
    async def test_upload_avatar_user_not_found(self):
        """Test avatar upload when user doesn't exist."""
        from routes.auth import upload_avatar
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import UploadFile
        from io import BytesIO
        import jwt
        import datetime
        
        payload = {
            'email': 'nonexistent@example.com',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        file_content = b'fake image data'
        file = UploadFile(filename='avatar.jpg', file=BytesIO(file_content))
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
            
            with pytest.raises(HTTPException) as exc_info:
                await upload_avatar(credentials, file)
            
            assert exc_info.value.status_code == 404


class TestGetCurrentUser:
    """Test get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful user retrieval."""
        from routes.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        import jwt
        import datetime
        
        payload = {
            'email': 'test@example.com',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        mock_user = {
            '_id': 'user123',
            'user_id': 'user123',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
            result = await get_current_user(credentials)
            
            assert result['email'] == 'test@example.com'
            assert result['user_id'] == 'user123'
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_email_in_token(self):
        """Test when token doesn't contain email."""
        from routes.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        import jwt
        import datetime
        
        payload = {
            'user_id': '123',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 403
        assert 'invalid' in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self):
        """Test when user doesn't exist in database."""
        from routes.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        import jwt
        import datetime
        
        payload = {
            'email': 'nonexistent@example.com',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)
            
            assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token(self):
        """Test with expired token."""
        from routes.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        import jwt
        import datetime
        
        payload = {
            'email': 'test@example.com',
            'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials=token)
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert 'expired' in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test with malformed token."""
        from routes.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        
        credentials = HTTPAuthorizationCredentials(scheme='Bearer', credentials='invalid.token.here')
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)
        
        assert exc_info.value.status_code == 401
        assert 'invalid' in exc_info.value.detail.lower()


class TestForgotPassword:
    """Test forgot password flow."""
    
    @pytest.mark.asyncio
    async def test_forgot_password_without_user(self):
        """Test forgot password when email not registered."""
        from routes.auth import forgot_password
        
        req = models.SendOTPRequest(email='unknown@example.com')
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            result = await forgot_password(req)
            
            # Should return success message even if user doesn't exist (security)
            assert 'message' in result
            assert 'registered' in result['message'].lower()


class TestResetPassword:
    """Test password reset functionality."""
    
    @pytest.mark.asyncio
    async def test_reset_password_missing_fields(self):
        """Test reset password with missing fields."""
        from routes.auth import reset_password
        
        # Missing new_password
        data = {'email': 'test@example.com', 'otp': '123456'}
        
        with pytest.raises(HTTPException) as exc_info:
            await reset_password(data)
        
        assert exc_info.value.status_code == 400
        assert 'missing' in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_otp(self):
        """Test reset password with invalid OTP."""
        from routes.auth import reset_password
        
        data = {
            'email': 'test@example.com',
            'otp': 'wrong',
            'new_password': 'NewPass123!'
        }
        
        with patch('routes.auth.otps_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await reset_password(data)
            
            assert exc_info.value.status_code == 400
            assert 'invalid' in exc_info.value.detail.lower() or 'expired' in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self):
        """Test reset password when user doesn't exist."""
        from routes.auth import reset_password
        
        data = {
            'email': 'nonexistent@example.com',
            'otp': '123456',
            'new_password': 'NewPass123!'
        }
        
        mock_otp = {'email': 'nonexistent@example.com', 'otp': '123456'}
        mock_update = Mock(modified_count=0)
        
        with patch('routes.auth.otps_col.find_one', new_callable=AsyncMock, return_value=mock_otp):
            with patch('routes.auth.users_col.update_one', new_callable=AsyncMock, return_value=mock_update):
                with pytest.raises(HTTPException) as exc_info:
                    await reset_password(data)
                
                assert exc_info.value.status_code == 404
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        """Test successful password reset."""
        from routes.auth import reset_password
        
        data = {
            'email': 'test@example.com',
            'otp': '123456',
            'new_password': 'NewPass123!'
        }
        
        mock_otp = {'email': 'test@example.com', 'otp': '123456'}
        mock_update = Mock(modified_count=1)
        mock_delete = AsyncMock()
        
        with patch('routes.auth.otps_col.find_one', new_callable=AsyncMock, return_value=mock_otp):
            with patch('routes.auth.users_col.update_one', new_callable=AsyncMock, return_value=mock_update):
                with patch('routes.auth.otps_col.delete_many', new_callable=AsyncMock, return_value=mock_delete.return_value):
                    result = await reset_password(data)
                    
                    assert 'message' in result
                    assert 'success' in result['message'].lower()


class TestDecodeJWT:
    """Test JWT decoding functionality."""
    
    def test_decode_jwt_success(self):
        """Test successful JWT decode."""
        from routes.auth import decode_jwt
        import jwt
        import datetime
        
        payload = {
            'email': 'test@example.com',
            'user_id': '123',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        decoded = decode_jwt(token)
        assert decoded['email'] == 'test@example.com'
        assert decoded['user_id'] == '123'
    
    def test_decode_jwt_expired(self):
        """Test decoding expired JWT."""
        from routes.auth import decode_jwt
        import jwt
        import datetime
        
        payload = {
            'email': 'test@example.com',
            'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(token)
        
        assert exc_info.value.status_code == 401
        assert 'expired' in exc_info.value.detail.lower()
    
    def test_decode_jwt_invalid(self):
        """Test decoding invalid JWT."""
        from routes.auth import decode_jwt
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt('invalid.token.string')
        
        assert exc_info.value.status_code == 401
        assert 'invalid' in exc_info.value.detail.lower()


class TestDecodeResetJWT:
    """Test decode_reset_jwt functionality."""
    
    def test_decode_reset_jwt_success(self):
        """Test successful reset JWT decode."""
        from utils.jwt_utils import create_reset_jwt, decode_reset_jwt
        
        email = "test@example.com"
        token = create_reset_jwt(email)
        decoded = decode_reset_jwt(token)
        
        assert decoded["sub"] == email
        assert decoded["purpose"] == "password_reset"
    
    def test_decode_reset_jwt_wrong_purpose(self):
        """Test decode_reset_jwt rejects token with wrong purpose."""
        from utils.jwt_utils import decode_reset_jwt
        import jwt
        import datetime
        
        payload = {
            "sub": "test@example.com",
            "purpose": "account_verification",  # Wrong purpose
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm=auth.JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt(token)
        
        assert exc_info.value.status_code == 401
        assert "purpose" in exc_info.value.detail.lower()
    
    def test_decode_reset_jwt_expired(self):
        """Test decode_reset_jwt handles expired token."""
        from utils.jwt_utils import decode_reset_jwt
        import jwt
        import datetime
        
        payload = {
            "sub": "test@example.com",
            "purpose": "password_reset",
            "exp": datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
        }
        token = jwt.encode(payload, auth.JWT_SECRET, algorithm=auth.JWT_ALGORITHM)
        
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_decode_reset_jwt_invalid(self):
        """Test decode_reset_jwt handles invalid token."""
        from utils.jwt_utils import decode_reset_jwt
        
        with pytest.raises(HTTPException) as exc_info:
            decode_reset_jwt("invalid.token")
        
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()


class TestResetPasswordEndpoint:
    """Test reset_password endpoint edge cases."""
    
    @pytest.mark.asyncio
    async def test_reset_password_missing_fields(self):
        """Test reset_password with missing fields."""
        from routes.auth import reset_password
        
        # Missing otp
        with pytest.raises(HTTPException) as exc_info:
            await reset_password({"email": "test@example.com", "new_password": "NewPass123!"})
        
        assert exc_info.value.status_code == 400
        assert "missing" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_invalid_otp(self):
        """Test reset_password with invalid OTP."""
        from routes.auth import reset_password
        
        with patch('routes.auth.otps_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await reset_password({
                    "email": "test@example.com",
                    "otp": "123456",
                    "new_password": "NewPass123!"
                })
            
            assert exc_info.value.status_code == 400
            assert "invalid" in exc_info.value.detail.lower() or "expired" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_user_not_found(self):
        """Test reset_password when user doesn't exist."""
        from routes.auth import reset_password
        
        mock_otp_doc = {"email": "test@example.com", "otp": "123456"}
        mock_update_result = Mock(modified_count=0)
        
        with patch('routes.auth.otps_col.find_one', new_callable=AsyncMock, return_value=mock_otp_doc):
            with patch('routes.auth.users_col.update_one', new_callable=AsyncMock, return_value=mock_update_result):
                with pytest.raises(HTTPException) as exc_info:
                    await reset_password({
                        "email": "test@example.com",
                        "otp": "123456",
                        "new_password": "NewPass123!"
                    })
                
                assert exc_info.value.status_code == 404
                assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_reset_password_success(self):
        """Test successful password reset."""
        from routes.auth import reset_password
        
        mock_otp_doc = {"email": "test@example.com", "otp": "123456"}
        mock_update_result = Mock(modified_count=1)
        
        with patch('routes.auth.otps_col.find_one', new_callable=AsyncMock, return_value=mock_otp_doc):
            with patch('routes.auth.users_col.update_one', new_callable=AsyncMock, return_value=mock_update_result):
                with patch('routes.auth.otps_col.delete_many', new_callable=AsyncMock):
                    result = await reset_password({
                        "email": "test@example.com",
                        "otp": "123456",
                        "new_password": "NewPass123!"
                    })
                    
                    assert result["message"] == "Password updated successfully"


class TestVerifyResetOTP:
    """Test verify_reset_otp endpoint."""
    
    @pytest.mark.asyncio
    async def test_verify_reset_otp_success(self):
        """Test successful reset OTP verification."""
        from routes.auth import verify_reset_otp
        from models import VerifyOTPRequest
        
        with patch('routes.auth.verify_otp_in_db', new_callable=AsyncMock, return_value=True):
            result = await verify_reset_otp(models.VerifyOTPRequest(email="Test@Example.com", otp="123456"))
            
            assert "reset_token" in result
            assert result["expires_in_minutes"] == auth.RESET_JWT_TTL_MINUTES
    
    @pytest.mark.asyncio
    async def test_verify_reset_otp_invalid(self):
        """Test verify_reset_otp with invalid OTP."""
        from routes.auth import verify_reset_otp
        from models import VerifyOTPRequest
        
        with patch('routes.auth.verify_otp_in_db', new_callable=AsyncMock, return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await verify_reset_otp(VerifyOTPRequest(email="test@example.com", otp="999999"))
            
            assert exc_info.value.status_code == 400
            assert "invalid" in exc_info.value.detail.lower() or "expired" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_verify_reset_otp_lowercase_email(self):
        """Test verify_reset_otp converts email to lowercase."""
        from routes.auth import verify_reset_otp
        from models import VerifyOTPRequest
        
        with patch('routes.auth.verify_otp_in_db', new_callable=AsyncMock, return_value=True) as mock_verify:
            await verify_reset_otp(VerifyOTPRequest(email="Test@Example.COM", otp="123456"))
            
            # Should be called with lowercase email
            mock_verify.assert_called_once_with("test@example.com", "123456")


class TestForgotPasswordLowercase:
    """Test forgot_password email lowercase handling."""
    
    @pytest.mark.asyncio
    async def test_forgot_password_lowercase_email(self):
        """Test forgot_password converts email to lowercase."""
        from routes.auth import forgot_password
        from models import SendOTPRequest
        
        mock_user = {"email": "test@example.com"}
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock) as mock_find:
            with patch('routes.auth.generate_otp', return_value="123456"):
                with patch('routes.auth.store_otp', new_callable=AsyncMock):
                    with patch('routes.auth.send_otp', new_callable=AsyncMock, return_value=True):
                        mock_find.return_value = mock_user
                        
                        await forgot_password(SendOTPRequest(email="Test@Example.COM"))
                        
                        # Should be called with lowercase email
                        mock_find.assert_called_once_with({"email": "test@example.com"})


class TestRegisterUserExistingEmail:
    """Test register_user with existing email."""
    
    @pytest.mark.asyncio
    async def test_register_existing_email(self):
        """Test registration fails when email already exists."""
        from routes.auth import register_user
        from models import RegisterRequest
        
        mock_existing = {"email": "existing@example.com"}
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=mock_existing):
            with pytest.raises(HTTPException) as exc_info:
                await register_user(RegisterRequest(
                    name="Test User",
                    email="existing@example.com",
                    password="Pass123!"
                ))
            
            assert exc_info.value.status_code == 400
            assert "already registered" in exc_info.value.detail.lower()


class TestLoginUserErrors:
    """Test login_user error paths."""
    
    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        """Test login with non-existent user."""
        from routes.auth import login_user
        from models import LoginRequest
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await login_user(LoginRequest(email="nonexistent@example.com", password="Pass123!"))
            
            assert exc_info.value.status_code == 400
            assert "not found" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_login_incorrect_password(self):
        """Test login with incorrect password."""
        from routes.auth import login_user
        from models import LoginRequest
        from utils.password_utils import pwd_context
        
        mock_user = {
            "email": "test@example.com",
            "password": pwd_context.hash("CorrectPass123!"),
            "verified": True,
            "_id": "user123"
        }
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=mock_user):
            with pytest.raises(HTTPException) as exc_info:
                await login_user(LoginRequest(email="test@example.com", password="WrongPass456!"))
            
            assert exc_info.value.status_code == 400
            assert "incorrect password" in exc_info.value.detail.lower()


class TestSendOTPUserNotFound:
    """Test send_otp when user doesn't exist."""
    
    @pytest.mark.asyncio
    async def test_send_otp_user_not_found(self):
        """Test send_otp fails for non-existent user."""
        from routes.auth import send_otp_router
        from models import SendOTPRequest
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await send_otp_router(SendOTPRequest(email="nonexistent@example.com"))
            
            assert exc_info.value.status_code == 400
            assert "not found" in exc_info.value.detail.lower()


class TestVerifyOTPInvalidOTP:
    """Test verify_otp with invalid OTP."""
    
    @pytest.mark.asyncio
    async def test_verify_otp_invalid(self):
        """Test verify_otp fails with invalid OTP."""
        from routes.auth import verify_otp
        from models import VerifyOTPRequest
        
        with patch('routes.auth.verify_otp_in_db', new_callable=AsyncMock, return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await verify_otp(VerifyOTPRequest(email="test@example.com", otp="999999"))
            
            assert exc_info.value.status_code == 400
            assert "invalid" in exc_info.value.detail.lower() or "expired" in exc_info.value.detail.lower()


class TestDecodeJWTExpiredToken:
    """Test decode_jwt with expired token."""
    
    def test_decode_jwt_expired_token(self):
        """Test decode_jwt raises HTTPException for expired token."""
        from utils.jwt_utils import decode_jwt
        import datetime
        
        payload = {
            'email': 'test@example.com',
            'exp': datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        }
        expired_token = jose_jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt(expired_token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_decode_jwt_invalid_token(self):
        """Test decode_jwt raises HTTPException for invalid token."""
        from utils.jwt_utils import decode_jwt
        
        with pytest.raises(HTTPException) as exc_info:
            decode_jwt("completely.invalid.token")
        
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()


class TestGetUserInfoEndpoint:
    """Test get_user_info endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_user_info_user_not_found_in_db(self):
        """Test get_user_info when user doesn't exist in database."""
        from routes.auth import get_user_info
        
        mock_credentials = Mock()
        payload = {
            'email': 'test@example.com',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        mock_credentials.credentials = jose_jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_user_info(credentials=mock_credentials)
            
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()


class TestUploadAvatarEndpoint:
    """Test upload_avatar endpoint."""
    
    @pytest.mark.asyncio
    async def test_upload_avatar_user_not_found_in_db(self):
        """Test upload_avatar when user doesn't exist in database."""
        from routes.auth import upload_avatar
        
        mock_credentials = Mock()
        payload = {
            'email': 'test@example.com',
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        mock_credentials.credentials = jose_jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        mock_file = Mock()
        mock_file.read = AsyncMock(return_value=b"fake_image_data")
        
        with patch('routes.auth.users_col.find_one', new_callable=AsyncMock, return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await upload_avatar(credentials=mock_credentials, file=mock_file)
            
            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()


class TestGetCurrentUserEdgeCases:
    """Test get_current_user edge cases."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_email_in_payload(self):
        """Test get_current_user when token has no email."""
        from routes.auth import get_current_user
        
        mock_credentials = Mock()
        payload = {
            'user_id': '123',  # No email field
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        mock_credentials.credentials = jose_jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)
        
        assert exc_info.value.status_code == 403
        assert "invalid token payload" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_expired_token_error(self):
        """Test get_current_user handles expired token."""
        from routes.auth import get_current_user
        
        mock_credentials = Mock()
        payload = {
            'email': 'test@example.com',
            'exp': datetime.utcnow() - timedelta(hours=1)  # Expired
        }
        mock_credentials.credentials = jose_jwt.encode(payload, auth.JWT_SECRET, algorithm='HS256')
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_error(self):
        """Test get_current_user handles invalid token."""
        from routes.auth import get_current_user
        
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=mock_credentials)
        
        assert exc_info.value.status_code == 401
        assert "invalid" in exc_info.value.detail.lower()

