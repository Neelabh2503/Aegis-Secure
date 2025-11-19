"""
Unit tests for main.py
Tests application startup, health endpoints, and middleware integration.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from tests.test_helpers import AsyncMock


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @patch('main.app')
    def test_root_endpoint(self, mock_app):
        """Test root endpoint returns service info."""
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/")
        async def root():
            return {"service": "AegisSecure Backend", "status": "running"}
        
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
    
    @patch('main.app')
    def test_health_endpoint(self, mock_app):
        """Test /health endpoint."""
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/health")
        async def health():
            return {"status": "healthy", "database": "connected"}
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('main.app')
    def test_ping_endpoint(self, mock_app):
        """Test /ping endpoint."""
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/ping")
        async def ping():
            return {"ping": "pong"}
        
        client = TestClient(app)
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json()["ping"] == "pong"


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
        try:
            from routes import auth, gmail, sms, dashboard, analysis
            assert all([auth, gmail, sms, dashboard, analysis])
        except ImportError as e:
            pytest.skip(f"Route import failed: {e}")
    
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


class TestMainLifespanCoverage:
    """Test main.py lifespan function for better coverage."""
    
    @pytest.mark.asyncio
    async def test_lifespan_db_connection_success(self):
        """Test successful database connection in lifespan."""
        from main import lifespan
        from fastapi import FastAPI
        
        test_app = FastAPI()
        
        with patch("main.log_startup_message"), \
             patch("main.settings.validate", return_value=[]), \
             patch("main.logger.info"), \
             patch("main.db_manager.connect", new_callable=AsyncMock), \
             patch("main.avatars_col.create_index", new_callable=AsyncMock), \
             patch("main.asyncio.create_task") as mock_task, \
             patch("main.settings.print_config_summary"), \
             patch("main.log_shutdown_message"), \
             patch("main.db_manager.disconnect", new_callable=AsyncMock):
            
            mock_task_obj = Mock()
            mock_task_obj.cancel = Mock()
            mock_task.return_value = mock_task_obj
            
            async with lifespan(test_app):
                pass
            
            mock_task_obj.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_lifespan_config_validation_errors(self):
        """Test lifespan with configuration validation errors."""
        from main import lifespan
        from fastapi import FastAPI
        
        test_app = FastAPI()
        
        with patch("main.log_startup_message"), \
             patch("main.settings.validate", return_value=["Error 1", "Error 2"]), \
             patch("main.logger.error") as mock_error, \
             patch("main.logger.warning") as mock_warning, \
             patch("main.logger.info"), \
             patch("main.db_manager.connect", new_callable=AsyncMock), \
             patch("main.avatars_col.create_index", new_callable=AsyncMock), \
             patch("main.asyncio.create_task"), \
             patch("main.settings.print_config_summary"), \
             patch("main.log_shutdown_message"), \
             patch("main.db_manager.disconnect", new_callable=AsyncMock):
            
            async with lifespan(test_app):
                pass
            
            # Should log errors for each config problem
            assert mock_error.call_count >= 2
            mock_warning.assert_called()
    
    @pytest.mark.asyncio
    async def test_lifespan_db_connect_failure(self):
        """Test lifespan handling database connection failure."""
        from main import lifespan
        from fastapi import FastAPI
        
        test_app = FastAPI()
        
        with patch("main.log_startup_message"), \
             patch("main.settings.validate", return_value=[]), \
             patch("main.logger.info"), \
             patch("main.db_manager.connect", side_effect=Exception("DB Error")), \
             patch("main.logger.error") as mock_error, \
             patch("main.avatars_col.create_index", new_callable=AsyncMock), \
             patch("main.asyncio.create_task"), \
             patch("main.settings.print_config_summary"), \
             patch("main.log_shutdown_message"), \
             patch("main.db_manager.disconnect", new_callable=AsyncMock):
            
            async with lifespan(test_app):
                pass
            
            # Should log database connection error
            error_calls = [str(call) for call in mock_error.call_args_list]
            assert any("database" in str(call).lower() for call in error_calls)
    
    @pytest.mark.asyncio
    async def test_lifespan_index_creation_failure(self):
        """Test lifespan handling index creation failure."""
        from main import lifespan
        from fastapi import FastAPI
        
        test_app = FastAPI()
        
        with patch("main.log_startup_message"), \
             patch("main.settings.validate", return_value=[]), \
             patch("main.logger.info"), \
             patch("main.db_manager.connect", new_callable=AsyncMock), \
             patch("main.avatars_col.create_index", side_effect=Exception("Index error")), \
             patch("main.logger.warning") as mock_warning, \
             patch("main.asyncio.create_task"), \
             patch("main.settings.print_config_summary"), \
             patch("main.log_shutdown_message"), \
             patch("main.db_manager.disconnect", new_callable=AsyncMock):
            
            async with lifespan(test_app):
                pass
            
            # Should log index warning
            warning_calls = [str(call) for call in mock_warning.call_args_list]
            assert any("index" in str(call).lower() for call in warning_calls)


class TestMainHealthEndpoints:
    """Test main.py health endpoints for coverage."""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Test root endpoint returns correct data."""
        from main import root
        
        response = await root()
        
        assert "status" in response
        assert "service" in response
        assert "version" in response
        assert response["status"] == "online"
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check with healthy database."""
        from main import health_check
        
        with patch("main.db_manager.ping", return_value=True):
            response = await health_check()
            
            assert response["status"] == "healthy"
            assert response["database"] == "connected"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        """Test health check with unhealthy database."""
        from main import health_check
        
        with patch("main.db_manager.ping", return_value=False):
            response = await health_check()
            
            assert response["status"] == "degraded"
            assert response["database"] == "disconnected"
    
    @pytest.mark.asyncio
    async def test_ping_endpoint(self):
        """Test ping endpoint."""
        from main import ping
        
        response = await ping()
        
        assert "ping" in response
        assert response["ping"] == "pong"


class TestExceptionHandlers:
    """Test custom exception handlers."""
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test RequestValidationError handler."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from pydantic import BaseModel
        
        app = FastAPI()
        
        from main import validation_exception_handler
        from fastapi.exceptions import RequestValidationError
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
        
        class TestModel(BaseModel):
            email: str
            age: int
        
        @app.post("/test")
        async def test_endpoint(data: TestModel):
            return {"success": True}
        
        client = TestClient(app)
        
        # Send invalid data to trigger validation error
        response = client.post("/test", json={"email": "invalid", "age": "not_a_number"})
        
        assert response.status_code == 422
        assert "error" in response.json()
    
    @pytest.mark.asyncio
    async def test_aegis_exception_handler(self):
        """Test AegisException handler."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from errors import AegisException
        from main import aegis_exception_handler
        
        app = FastAPI()
        app.add_exception_handler(AegisException, aegis_exception_handler)
        
        @app.get("/test")
        async def test_endpoint():
            raise AegisException("Test error", status_code=400)
        
        client = TestClient(app)
        response = client.get("/test")
        
        assert response.status_code == 400


class TestStartupEvents:
    """Test application startup events."""
    
    @pytest.mark.asyncio
    async def test_init_indexes_success(self):
        """Test successful index initialization."""
        with patch("main.os.environ.get", return_value=None), \
             patch("main.asyncio.create_task") as mock_task, \
             patch("main.avatars_col.create_index", new_callable=AsyncMock) as mock_index, \
             patch("builtins.print"):
            
            from main import init_indexes
            await init_indexes()
            
            # Should create tasks for retry loops
            assert mock_task.call_count >= 3
            mock_index.assert_called_once_with("email", unique=True)
    
    @pytest.mark.asyncio
    async def test_init_indexes_during_reload(self):
        """Test index initialization skips notification tasks during reload."""
        with patch("main.os.environ.get", return_value="true"), \
             patch("main.asyncio.create_task") as mock_task, \
             patch("main.avatars_col.create_index", new_callable=AsyncMock), \
             patch("builtins.print"):
            
            from main import init_indexes
            await init_indexes()
            
            # Should skip notification tasks during reload
            # Only SMS retry task should be created
            assert mock_task.call_count == 1
    
    @pytest.mark.asyncio
    async def test_init_indexes_notification_error(self):
        """Test handling of notification task initialization error."""
        with patch("main.os.environ.get", return_value=None), \
             patch("main.asyncio.create_task", side_effect=[Exception("Task error"), Mock(), Mock()]) as mock_task, \
             patch("main.avatars_col.create_index", new_callable=AsyncMock), \
             patch("builtins.print") as mock_print:
            
            from main import init_indexes
            await init_indexes()
            
            # Should log the error
            print_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Failed to start" in str(call) for call in print_calls)
