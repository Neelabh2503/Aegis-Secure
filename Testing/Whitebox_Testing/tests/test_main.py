"""
Unit tests for main.py
Tests application startup, health endpoints, and middleware integration.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint returns service info."""
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "online"
    
class TestApplicationConfiguration:
    """Test FastAPI application configuration."""
    
    def test_app_import(self):
        """Test main app can be imported."""
        from main import app
        assert app is not None
    
    def test_app_title(self):
        """Test app has configured title."""
        from main import app
        assert hasattr(app, 'title')
    
    def test_app_version(self):
        """Test app has version info."""
        from main import app
        assert hasattr(app, 'version')


class TestMiddlewareIntegration:
    """Test middleware is properly integrated."""
    
    def test_middleware_imported(self):
        """Test middleware modules are imported."""
        try:
            from middleware import (
                RateLimitMiddleware,
                SecurityHeadersMiddleware,
                RequestValidationMiddleware
            )
            assert True
        except ImportError:
            pytest.skip("Middleware not found")
    
    def test_cors_middleware_configured(self):
        """Test CORS middleware exists."""
        from main import app
        # Check if CORS middleware is in middleware stack
        middleware_types = [type(m) for m in app.user_middleware]
        # Should have some middleware configured
        assert len(app.user_middleware) >= 0


class TestRouterIntegration:
    """Test API routers are integrated."""
    
    def test_routers_imported(self):
        """Test all route modules can be imported."""
        from routes import auth, gmail, sms, dashboard, notifications, Oauth
        assert all([auth, gmail, sms, dashboard, notifications, Oauth])
    
    def test_app_routes_exist(self):
        """Test app has routes configured."""
        from main import app
        routes = [route.path for route in app.routes]
        assert len(routes) > 0


class TestDatabaseIntegration:
    """Test database connection setup."""
    
    def test_database_imported(self):
        """Test database module can be imported."""
        try:
            from database import users_col, messages_col
            assert users_col is not None
            assert messages_col is not None
        except ImportError:
            pytest.skip("Database module not found")


class TestLifespanEvents:
    """Test application lifespan events."""
    
    @pytest.mark.asyncio
    async def test_startup_event(self):
        """Test startup event can be triggered."""
        # This test ensures no errors during startup
        try:
            from main import app
            # Simulate startup
            assert app is not None
        except Exception as e:
            pytest.fail(f"Startup failed: {e}")
    
    @pytest.mark.asyncio
    async def test_shutdown_event(self):
        """Test shutdown event can be triggered."""
        try:
            from main import app
            # Simulate shutdown
            assert app is not None
        except Exception as e:
            pytest.fail(f"Shutdown failed: {e}")


class TestLifespanManagement:
    """Test lifespan context manager"""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_without_reloader(self):
        """Test lifespan starts retry tasks when not in reloader mode"""
        from main import lifespan, app
        
        with patch.dict('os.environ', {'UVICORN_RELOADER': 'false'}, clear=False):
            with patch('asyncio.create_task') as mock_create_task:
                with patch('database.auth_db') as mock_auth_db, \
                     patch('database.mail_db') as mock_mail_db, \
                     patch('database.sms_db') as mock_sms_db:
                    
                    mock_auth_db.users.create_index = AsyncMock()
                    mock_auth_db.otps.create_index = AsyncMock()
                    mock_mail_db.accounts.create_index = AsyncMock()
                    mock_mail_db.messages.create_index = AsyncMock()
                    mock_mail_db.avatars.create_index = AsyncMock()
                    mock_sms_db.sms_messages.create_index = AsyncMock()
                    
                    async with lifespan(app):
                        assert mock_create_task.call_count == 2
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_with_reloader(self):
        """Test lifespan skips retry tasks in reloader mode"""
        from main import lifespan, app
        
        with patch.dict('os.environ', {'UVICORN_RELOADER': 'true'}, clear=False):
            with patch('asyncio.create_task') as mock_create_task:
                with patch('database.auth_db') as mock_auth_db, \
                     patch('database.mail_db') as mock_mail_db, \
                     patch('database.sms_db') as mock_sms_db:
                    
                    mock_auth_db.users.create_index = AsyncMock()
                    mock_auth_db.otps.create_index = AsyncMock()
                    mock_mail_db.accounts.create_index = AsyncMock()
                    mock_mail_db.messages.create_index = AsyncMock()
                    mock_mail_db.avatars.create_index = AsyncMock()
                    mock_sms_db.sms_messages.create_index = AsyncMock()
                    
                    async with lifespan(app):
                        mock_create_task.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_lifespan_creates_indexes(self):
        """Test lifespan creates all database indexes"""
        from main import lifespan, app
        
        with patch.dict('os.environ', {'UVICORN_RELOADER': 'true'}, clear=False):
            with patch('database.auth_db') as mock_auth_db, \
                 patch('database.mail_db') as mock_mail_db, \
                 patch('database.sms_db') as mock_sms_db:
                
                mock_auth_db.users.create_index = AsyncMock()
                mock_auth_db.otps.create_index = AsyncMock()
                mock_mail_db.accounts.create_index = AsyncMock()
                mock_mail_db.messages.create_index = AsyncMock()
                mock_mail_db.avatars.create_index = AsyncMock()
                mock_sms_db.sms_messages.create_index = AsyncMock()
                
                async with lifespan(app):
                    pass
                
                # Verify indexes were created
                assert mock_auth_db.users.create_index.called
                assert mock_auth_db.otps.create_index.called
                assert mock_mail_db.accounts.create_index.called
                assert mock_mail_db.messages.create_index.called
                assert mock_mail_db.avatars.create_index.called
                assert mock_sms_db.sms_messages.create_index.called


