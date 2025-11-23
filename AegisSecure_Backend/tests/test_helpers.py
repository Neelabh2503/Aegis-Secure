"""
Test helpers and utilities for async testing.
"""
from unittest.mock import AsyncMock


class AsyncContextManagerMock:
    """Mock async context manager for httpx.AsyncClient and similar."""
    def __init__(self, return_value):
        self.return_value = return_value
    
    async def __aenter__(self):
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None
