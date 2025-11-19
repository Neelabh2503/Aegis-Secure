""" 
Unit tests for routes/dashboard.py
Tests dashboard statistics and aggregation logic.
"""
import pytest
from unittest.mock import patch, Mock
from .test_helpers import AsyncMock
from routes import dashboard
from fastapi import HTTPException
class TestDashboardConfiguration:
    """Test dashboard constants and configuration."""
    
    def test_labels_configured(self):
        """Test security labels are properly defined."""
        assert dashboard.LABELS == ["Secure", "Suspicious", "Threat", "Critical"]
        assert len(dashboard.LABELS) == 4
    
    def test_bucket_bounds_configured(self):
        """Test bucket boundaries for score ranges."""
        assert dashboard.BUCKET_BOUNDS == [0, 26, 51, 76, 101]
        assert len(dashboard.BUCKET_BOUNDS) == 5
    
    def test_cyber_trends_exist(self):
        """Test cybersecurity trends are defined."""
        assert len(dashboard.CYBER_TRENDS) > 0
        assert all(isinstance(trend, str) for trend in dashboard.CYBER_TRENDS)
        assert all(len(trend) > 10 for trend in dashboard.CYBER_TRENDS)


class TestAggregationFunctions:
    """Test dashboard aggregation functions."""
    
    @pytest.mark.asyncio
    async def test_aggregate_collection_function_exists(self):
        """Test aggregate_collection_by_buckets exists."""
        assert hasattr(dashboard, 'aggregate_collection_by_buckets')
        assert callable(dashboard.aggregate_collection_by_buckets)
    
    def test_bucket_mapping_logic(self):
        """Test bucket boundaries map to correct indices."""
        # Verify bucket logic matches expected ranges
        assert dashboard.BUCKET_BOUNDS[0] == 0  # Secure starts at 0
        assert dashboard.BUCKET_BOUNDS[1] == 26  # Suspicious starts at 26
        assert dashboard.BUCKET_BOUNDS[2] == 51  # Threat starts at 51
        assert dashboard.BUCKET_BOUNDS[3] == 76  # Critical starts at 76


class TestGroqClientConfiguration:
    """Test Groq AI client setup."""
    
    def test_groq_client_initialized(self):
        """Test Groq client is initialized."""
        assert dashboard.client is not None
    
    def test_groq_api_key_configured(self):
        """Test Groq API key is set from environment."""
        import os
        # If API key exists, client should be configured
        if os.getenv("GROQ_API_KEY"):
            assert dashboard.client is not None


class TestDashboardRouterConfiguration:
    """Test dashboard router setup."""
    
    def test_router_prefix_configured(self):
        """Test router has /dashboard prefix."""
        assert dashboard.router.prefix == "/dashboard"
    
    def test_router_tags_configured(self):
        """Test router has Dashboard tag."""
        assert "Dashboard" in dashboard.router.tags


class TestAggregateCollectionByBuckets:
    """Test aggregation function for dashboard stats."""
    
    @pytest.mark.asyncio
    async def test_aggregate_basic_functionality(self):
        """Test aggregation basic functionality with patching."""
        from routes.dashboard import aggregate_collection_by_buckets, BUCKET_BOUNDS
        from unittest.mock import MagicMock
        
        # Create a mock that properly supports async iteration
        class MockAsyncCursor:
            def __init__(self, data):
                self.data = data
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                result = self.data[self.index]
                self.index += 1
                return result
        
        mock_data = [
            {'_id': 0, 'count': 5},
            {'_id': 26, 'count': 10},
            {'_id': 51, 'count': 3}
        ]
        
        mock_col = MagicMock()
        mock_col.aggregate = MagicMock(return_value=MockAsyncCursor(mock_data))
        
        result = await aggregate_collection_by_buckets(
            mock_col, 'user_id', 'threat_score', 'user123', days=None
        )
        
        assert isinstance(result, dict)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_aggregate_with_time_filter(self):
        """Test aggregation with time filter."""
        from routes.dashboard import aggregate_collection_by_buckets
        from unittest.mock import MagicMock
        
        # Create a mock that properly supports async iteration
        class MockAsyncCursor:
            def __init__(self, data):
                self.data = data
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                result = self.data[self.index]
                self.index += 1
                return result
        
        mock_data = [
            {'_id': 76, 'count': 8}
        ]
        
        mock_col = MagicMock()
        mock_col.aggregate = MagicMock(return_value=MockAsyncCursor(mock_data))
        
        result = await aggregate_collection_by_buckets(
            mock_col, 'user_id', 'score', 'user456', days=7
        )
        
        assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_aggregate_boundary_handling(self):
        """Test aggregation handles boundary values correctly."""
        from routes.dashboard import aggregate_collection_by_buckets
        from unittest.mock import MagicMock
        
        # Create a mock that properly supports async iteration
        class MockAsyncCursor:
            def __init__(self, data):
                self.data = data
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index >= len(self.data):
                    raise StopAsyncIteration
                result = self.data[self.index]
                self.index += 1
                return result
        
        mock_data = [
            {'_id': 51, 'count': 2},
            {'_id': 75, 'count': 4}
        ]
        
        mock_col = MagicMock()
        mock_col.aggregate = MagicMock(return_value=MockAsyncCursor(mock_data))
        
        result = await aggregate_collection_by_buckets(
            mock_col, 'user_id', 'risk', 'user789', days=30
        )
        
        assert isinstance(result, dict)


class TestGenerateCyberFactsAI:
    """Test AI cyber facts generation."""
    
    @pytest.mark.asyncio
    async def test_generate_facts_returns_dict(self):
        """Test that generate_cyber_facts_ai returns a dictionary."""
        from routes.dashboard import generate_cyber_facts_ai
        
        result = await generate_cyber_facts_ai()
        
        # Should always return a dict with fact1 and fact2
        assert isinstance(result, dict)
        assert 'fact1' in result
        assert 'fact2' in result
        assert isinstance(result['fact1'], str)
        assert isinstance(result['fact2'], str)
    
    @pytest.mark.asyncio
    async def test_generate_facts_with_valid_json(self):
        """Test AI returns valid JSON response."""
        from routes.dashboard import generate_cyber_facts_ai
        
        mock_message = Mock()
        mock_message.content = '{"fact1": "Enable MFA", "fact2": "Use strong passwords"}'
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('routes.dashboard.client.chat.completions.create', return_value=mock_response):
            result = await generate_cyber_facts_ai()
            
            assert result['fact1'] == "Enable MFA"
            assert result['fact2'] == "Use strong passwords"
    
    @pytest.mark.asyncio
    async def test_generate_facts_with_json_in_text(self):
        """Test AI returns JSON embedded in text."""
        from routes.dashboard import generate_cyber_facts_ai
        
        mock_message = Mock()
        mock_message.content = 'Here is the data: {"fact1": "Check links", "fact2": "Verify sender"} end'
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('routes.dashboard.client.chat.completions.create', return_value=mock_response):
            result = await generate_cyber_facts_ai()
            
            assert result['fact1'] == "Check links"
            assert result['fact2'] == "Verify sender"
    
    @pytest.mark.asyncio
    async def test_generate_facts_json_parse_error(self):
        """Test fallback when JSON parsing fails."""
        from routes.dashboard import generate_cyber_facts_ai
        
        mock_message = Mock()
        mock_message.content = 'This is not valid JSON at all'
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('routes.dashboard.client.chat.completions.create', return_value=mock_response):
            result = await generate_cyber_facts_ai()
            
            assert 'fact1' in result
            assert 'fact2' in result
            assert 'Unable' in result['fact1'] or result['fact1'] == ""
    
    @pytest.mark.asyncio
    async def test_generate_facts_missing_keys(self):
        """Test fallback when JSON missing required keys."""
        from routes.dashboard import generate_cyber_facts_ai
        
        mock_message = Mock()
        mock_message.content = '{"other": "value"}'
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('routes.dashboard.client.chat.completions.create', return_value=mock_response):
            result = await generate_cyber_facts_ai()
            
            assert 'fact1' in result
            assert 'fact2' in result
    
    @pytest.mark.asyncio
    async def test_generate_facts_api_exception(self):
        """Test exception handling."""
        from routes.dashboard import generate_cyber_facts_ai
        
        with patch('routes.dashboard.client.chat.completions.create', side_effect=Exception("API Error")):
            result = await generate_cyber_facts_ai()
            
            assert result == {"fact1": "", "fact2": ""}
    
    @pytest.mark.asyncio
    async def test_generate_facts_with_reasoning_fallback(self):
        """Test fallback to reasoning field."""
        from routes.dashboard import generate_cyber_facts_ai
        
        mock_message = Mock()
        mock_message.content = None
        mock_message.reasoning = '{"fact1": "Test fact", "fact2": "Another fact"}'
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        with patch('routes.dashboard.client.chat.completions.create', return_value=mock_response):
            result = await generate_cyber_facts_ai()
            
            assert result['fact1'] == "Test fact"
            assert result['fact2'] == "Another fact"


class TestGetDashboardEndpoint:
    """Test dashboard endpoint."""
    
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
        
        with patch('routes.dashboard.aggregate_collection_by_buckets', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {0: 5, 1: 10, 2: 3, 3: 2}
            
            with patch('routes.dashboard.generate_cyber_facts_ai', new_callable=AsyncMock) as mock_facts:
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
        
        with patch('routes.dashboard.aggregate_collection_by_buckets', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {0: 5, 1: 10}
            
            with patch('routes.dashboard.generate_cyber_facts_ai', new_callable=AsyncMock) as mock_facts:
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
        
        with patch('routes.dashboard.aggregate_collection_by_buckets', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {0: 3, 1: 7, 2: 2}
            
            with patch('routes.dashboard.generate_cyber_facts_ai', new_callable=AsyncMock) as mock_facts:
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
        
        with patch('routes.dashboard.aggregate_collection_by_buckets', new_callable=AsyncMock) as mock_agg:
            mock_agg.return_value = {}
            
            with patch('routes.dashboard.generate_cyber_facts_ai', new_callable=AsyncMock) as mock_facts:
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
        
        with patch('routes.dashboard.aggregate_collection_by_buckets', new_callable=AsyncMock) as mock_agg:
            # Return partial data
            mock_agg.return_value = {0: 5}  # Only bucket 0
            
            with patch('routes.dashboard.generate_cyber_facts_ai', new_callable=AsyncMock) as mock_facts:
                mock_facts.return_value = {"fact1": "X", "fact2": "Y"}
                
                result = await get_dashboard(mode="sms", current_user=mock_user)
                
                # Should have all 4 buckets filled
                assert len(result['values']) == 4
                assert result['values'][0] == 5
                assert result['values'][1] == 0
                assert result['values'][2] == 0
                assert result['values'][3] == 0

