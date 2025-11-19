"""
Pytest configuration and shared fixtures for testing.
"""
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from httpx import AsyncClient
from fastapi.testclient import TestClient
import os
import sys
from unittest.mock import MagicMock


# Python 3.7 compatible AsyncMock
class AsyncMock(MagicMock):
    """AsyncMock for Python 3.7 compatibility."""
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import config first (doesn't need firebase)
from config import settings
from database import users_col, otps_col, messages_col, accounts_col

# Mock firebase if not available
try:
    import firebase_admin
except ImportError:
    import unittest.mock as mock
    sys.modules['firebase_admin'] = mock.MagicMock()
    sys.modules['firebase_admin.messaging'] = mock.MagicMock()
    sys.modules['firebase_admin.credentials'] = mock.MagicMock()

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_db():
    """Create a test database connection."""
    # Use a separate test database
    test_mongo_uri = os.getenv("TEST_MONGO_URI", settings.MONGO_URI)
    client = AsyncIOMotorClient(test_mongo_uri)
    test_db = client.test_aegis_secure
    
    yield test_db
    
    # Cleanup after tests
    await client.drop_database("test_aegis_secure")
    client.close()


@pytest.fixture
async def clean_db():
    """Clean test data before each test."""
    # Clear test collections
    await users_col.delete_many({"email": {"$regex": "test.*@test.com"}})
    await otps_col.delete_many({"email": {"$regex": "test.*@test.com"}})
    await messages_col.delete_many({"user_id": {"$regex": "test_.*"}})
    await accounts_col.delete_many({"user_id": {"$regex": "test_.*"}})
    yield
    # Cleanup after test
    await users_col.delete_many({"email": {"$regex": "test.*@test.com"}})
    await otps_col.delete_many({"email": {"$regex": "test.*@test.com"}})


@pytest.fixture
def test_user_data():
    """Sample test user data."""
    return {
        "name": "Test User",
        "email": "test@test.com",
        "password": "SecureP@ss123"
    }


@pytest.fixture
def test_weak_password():
    """Weak password for validation testing."""
    return "weak"


@pytest.fixture
def test_strong_password():
    """Strong password for validation testing."""
    return "SecureP@ssw0rd!"


@pytest.fixture
async def authenticated_user(client, test_user_data, clean_db):
    """Create and authenticate a test user, return JWT token."""
    # Register user
    register_response = client.post("/auth/register", json=test_user_data)
    assert register_response.status_code == 201
    
    # Mark user as verified (bypass OTP for testing)
    await users_col.update_one(
        {"email": test_user_data["email"]},
        {"$set": {"verified": True}}
    )
    
    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]
    
    return {
        "token": token,
        "user_data": test_user_data
    }


@pytest.fixture
def auth_headers(authenticated_user):
    """Get authorization headers with JWT token."""
    return {"Authorization": f"Bearer {authenticated_user['token']}"}
