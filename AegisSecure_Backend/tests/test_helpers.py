"""
Test helpers for Python 3.7 compatibility.
"""
from unittest.mock import MagicMock


class AsyncMock(MagicMock):
    """
    AsyncMock for Python 3.7 compatibility.
    This allows mocking async functions in Python 3.7 where AsyncMock doesn't exist.
    """
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class AsyncContextManagerMock:
    """Mock async context manager for httpx.AsyncClient and similar."""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None
