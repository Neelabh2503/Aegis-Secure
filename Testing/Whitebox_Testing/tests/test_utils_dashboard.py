"""
Tests for dashboard utility functions
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from utils.dashboard_utils import grouped_data_fromDB, generate_Cyber_insights, BOUNDARIES


class TestGroupedDataFromDB:
    """Test grouped_data_fromDB aggregation function"""
    
    @pytest.mark.asyncio
    async def test_grouped_data_basic(self):
        """Test basic aggregation without days filter"""
        mock_col = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = iter([
            {"_id": 0, "count": 5},
            {"_id": 26, "count": 10},
            {"_id": 51, "count": 3}
        ])
        mock_col.aggregate = Mock(return_value=mock_cursor)
        
        result = await grouped_data_fromDB(mock_col, "user_id", "spam_score", "user123", None)
        
        assert result[0] == 5
        assert result[1] == 10
        assert result[2] == 3
    
    @pytest.mark.asyncio
    async def test_grouped_data_with_days_filter(self):
        """Test aggregation with time filter"""
        mock_col = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = iter([{"_id": 0, "count": 2}])
        mock_col.aggregate = Mock(return_value=mock_cursor)
        
        result = await grouped_data_fromDB(mock_col, "user_id", "spam_score", "user123", 7)
        
        assert mock_col.aggregate.called
        assert result[0] == 2
    
    @pytest.mark.asyncio
    async def test_grouped_data_empty_result(self):
        """Test with no data"""
        mock_col = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = iter([])
        mock_col.aggregate = Mock(return_value=mock_cursor)
        
        result = await grouped_data_fromDB(mock_col, "user_id", "spam_score", "user123", None)
        
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_grouped_data_boundary_mapping(self):
        """Test that boundaries are correctly mapped to indices"""
        mock_col = Mock()
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = iter([
            {"_id": 0, "count": 1},
            {"_id": 26, "count": 2},
            {"_id": 51, "count": 3},
            {"_id": 76, "count": 4}
        ])
        mock_col.aggregate = Mock(return_value=mock_cursor)
        
        result = await grouped_data_fromDB(mock_col, "user_id", "spam_score", "user123", None)
        
        assert result[0] == 1  # 0-25
        assert result[1] == 2  # 26-50
        assert result[2] == 3  # 51-75
        assert result[3] == 4  # 76-100


class TestGenerateCyberInsights:
    """Test AI insights generation"""
    
    @pytest.mark.asyncio
    async def test_generate_insights_success(self):
        """Test successful insights generation"""
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = '{"fact1": "Use strong passwords", "fact2": "Enable 2FA"}'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch('utils.dashboard_utils.client.chat.completions.create', return_value=mock_response):
            result = await generate_Cyber_insights()
            
            assert "fact1" in result
            assert "fact2" in result
            assert result["fact1"] == "Use strong passwords"
            assert result["fact2"] == "Enable 2FA"
    
    @pytest.mark.asyncio
    async def test_generate_insights_json_in_markdown(self):
        """Test JSON extraction from markdown"""
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = 'Some text\n```json\n{"fact1": "Tip 1", "fact2": "Tip 2"}\n```\nMore text'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch('utils.dashboard_utils.client.chat.completions.create', return_value=mock_response):
            result = await generate_Cyber_insights()
            
            assert result["fact1"] == "Tip 1"
            assert result["fact2"] == "Tip 2"
    
    @pytest.mark.asyncio
    async def test_generate_insights_fallback_on_error(self):
        """Test fallback when API fails"""
        with patch('utils.dashboard_utils.client.chat.completions.create', side_effect=Exception("API Error")):
            result = await generate_Cyber_insights()
            
            assert "fact1" in result
            assert "fact2" in result
            # Should return empty strings on complete failure
            assert result["fact1"] == ""
            assert result["fact2"] == ""
    
    @pytest.mark.asyncio
    async def test_generate_insights_invalid_json(self):
        """Test handling of invalid JSON response"""
        mock_response = Mock()
        mock_message = Mock()
        mock_message.content = 'This is not valid JSON'
        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch('utils.dashboard_utils.client.chat.completions.create', return_value=mock_response):
            result = await generate_Cyber_insights()
            
            assert "fact1" in result
            assert "Unable to fetch" in result["fact1"] or result["fact1"] == ""


class TestBoundariesConfiguration:
    """Test BOUNDARIES constant"""
    
    def test_boundaries_defined(self):
        """Test BOUNDARIES is properly defined"""
        assert BOUNDARIES == [0, 26, 51, 76, 101]
    
    def test_boundaries_length(self):
        """Test BOUNDARIES has correct number of elements"""
        assert len(BOUNDARIES) == 5
