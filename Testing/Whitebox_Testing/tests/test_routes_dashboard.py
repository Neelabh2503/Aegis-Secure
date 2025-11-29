""" 
Unit tests for routes/dashboard.py
Tests dashboard statistics and aggregation logic.
"""
import pytest
from unittest.mock import patch, Mock
from .test_helpers import AsyncMock
from routes import dashboard
from utils import dashboard_utils
from fastapi import HTTPException
class TestDashboardConfiguration:
    """Test dashboard constants and configuration."""
    
    def test_labels_configured(self):
        """Test security labels are properly defined."""
        assert dashboard.LABELS == ["Secure", "Suspicious", "Threat", "Critical"]
        assert len(dashboard.LABELS) == 4
    
    def test_bucket_bounds_configured(self):
        """Test bucket boundaries for score ranges."""
        assert dashboard_utils.BOUNDARIES == [0, 26, 51, 76, 101]
        assert len(dashboard_utils.BOUNDARIES) == 5
    
class TestAggregationFunctions:
    """Test dashboard aggregation functions."""
    
    @pytest.mark.asyncio
    async def test_aggregate_collection_function_exists(self):
        """Test grouped_data_fromDB exists in utils."""
        assert hasattr(dashboard_utils, 'grouped_data_fromDB')
        assert callable(dashboard_utils.grouped_data_fromDB)
    
    def test_bucket_mapping_logic(self):
        """Test bucket boundaries map to correct indices."""
        # Verify bucket logic matches expected ranges
        assert dashboard_utils.BOUNDARIES[0] == 0  # Secure starts at 0
        assert dashboard_utils.BOUNDARIES[1] == 26  # Suspicious starts at 26
        assert dashboard_utils.BOUNDARIES[2] == 51  # Threat starts at 51
        assert dashboard_utils.BOUNDARIES[3] == 76  # Critical starts at 76


class TestGroqClientConfiguration:
    """Test Groq AI client setup."""
    
    def test_groq_client_initialized(self):
        """Test Groq client is initialized."""
        assert dashboard_utils.client is not None
    
    def test_groq_api_key_configured(self):
        """Test Groq API key is set from environment."""
        import os
        # If API key exists, client should be configured
        if os.getenv("GROQ_API_KEY"):
            assert dashboard_utils.client is not None


class TestDashboardRouterConfiguration:
    """Test dashboard router setup."""
    
    def test_router_prefix_configured(self):
        """Test router has /dashboard prefix."""
        assert dashboard.router.prefix == "/dashboard"
    
    def test_router_tags_configured(self):
        """Test router has Dashboard tag."""
        assert "Dashboard" in dashboard.router.tags


class TestGetDashboardEndpoint:
    """Test /dashboard endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_dashboard_no_user_id(self):
        """Test dashboard requires user ID."""
        from routes.dashboard import get_dashboard
        
        mock_user = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_dashboard(current_user=mock_user)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_dashboard_both_mode(self):
        """Test dashboard with both SMS and mail."""
        from routes.dashboard import get_dashboard
        
        mock_user = {"user_id": "user123"}
        
        with patch('routes.dashboard.grouped_data_fromDB', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {0: 5, 1: 10, 2: 3, 3: 2}
            
            with patch('routes.dashboard.generate_Cyber_insights', new_callable=AsyncMock) as mock_facts:
                mock_facts.return_value = {"fact1": "Test fact 1", "fact2": "Test fact 2"}
                
                result = await get_dashboard(mode="both", current_user=mock_user)
                
                assert result['labels'] == ["Secure", "Suspicious", "Threat", "Critical"]
                assert len(result['values']) == 4
                assert 'total' in result
                assert 'insights' in result
                assert mock_agg.call_count == 2  # Called for both sms and mail
    
    @pytest.mark.asyncio
    async def test_get_dashboard_sms_only(self):
        """Test dashboard with SMS only."""
        from routes.dashboard import get_dashboard
        
        mock_user = {"user_id": "user123"}
        
        with patch('routes.dashboard.grouped_data_fromDB', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {0: 5, 1: 10}
            
            with patch('routes.dashboard.generate_Cyber_insights', new_callable=AsyncMock) as mock_facts:
                mock_facts.return_value = {"fact1": "Test", "fact2": "Test2"}
                
                result = await get_dashboard(mode="sms", current_user=mock_user)
                
                assert result['values'][0] == 5
                assert result['values'][1] == 10
                assert mock_agg.call_count == 1  # Only called once for SMS
    
    @pytest.mark.asyncio
    async def test_get_dashboard_mail_only(self):
        """Test dashboard with mail only."""
        from routes.dashboard import get_dashboard
        
        mock_user = {"user_id": "user123"}
        
        with patch('routes.dashboard.grouped_data_fromDB', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {0: 3, 1: 7, 2: 2}
            
            with patch('routes.dashboard.generate_Cyber_insights', new_callable=AsyncMock) as mock_facts:
                mock_facts.return_value = {"fact1": "Tip1", "fact2": "Tip2"}
                
                result = await get_dashboard(mode="mail", current_user=mock_user)
                
                assert result['values'][0] == 3
                assert result['values'][1] == 7
                assert mock_agg.call_count == 1  # Only called once for mail
    
    @pytest.mark.asyncio
    async def test_get_dashboard_with_days_filter(self):
        """Test dashboard with time filter."""
        from routes.dashboard import get_dashboard
        
        mock_user = {"user_id": "user123"}
        
        with patch('routes.dashboard.grouped_data_fromDB', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {}
            
            with patch('routes.dashboard.generate_Cyber_insights', new_callable=AsyncMock) as mock_facts:
                mock_facts.return_value = {"fact1": "A", "fact2": "B"}
                
                result = await get_dashboard(mode="both", days=7, current_user=mock_user)
                
                # Verify days parameter was passed
                assert mock_agg.called
                assert mock_agg.call_count == 2  # Called for both sms and mail
    
    @pytest.mark.asyncio
    async def test_get_dashboard_fills_missing_buckets(self):
        """Test dashboard fills in missing bucket counts."""
        from routes.dashboard import get_dashboard
        
        mock_user = {"user_id": "user123"}
        
        with patch('routes.dashboard.grouped_data_fromDB', new_callable=AsyncMock) as mock_agg:
            # Return partial data
            mock_agg.return_value = {0: 5}  # Only bucket 0
            
            with patch('routes.dashboard.generate_Cyber_insights', new_callable=AsyncMock) as mock_facts:
                mock_facts.return_value = {"fact1": "X", "fact2": "Y"}
                
                result = await get_dashboard(mode="sms", current_user=mock_user)
                
                # Should have all 4 buckets filled
                assert len(result['values']) == 4
                assert result['values'][0] == 5
                assert result['values'][1] == 0
                assert result['values'][2] == 0
                assert result['values'][3] == 0

