"""
Tests for color decoration utility functions
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from utils.Color_decoration_utils import get_sender_avatar_color, COLOR_PALETTE


class TestColorPalette:
    """Test COLOR_PALETTE configuration"""
    
    def test_color_palette_exists(self):
        """Test that COLOR_PALETTE is defined"""
        assert COLOR_PALETTE is not None
    
    def test_color_palette_is_list(self):
        """Test that COLOR_PALETTE is a list"""
        assert isinstance(COLOR_PALETTE, list)


class TestGetSenderAvatarColor:
    """Test get_sender_avatar_color function"""
    
    @pytest.mark.asyncio
    async def test_returns_existing_color(self):
        """Test returning existing color for sender"""
        mock_doc = {"email": "test@example.com", "char_color": "#FF0000"}
        
        with patch('utils.Color_decoration_utils.avatars_col.find_one', new_callable=AsyncMock, return_value=mock_doc):
            color = await get_sender_avatar_color("test@example.com")
            assert color == "#FF0000"
    
    @pytest.mark.asyncio
    async def test_assigns_new_color_if_not_exists(self):
        """Test assigning new color when sender doesn't have one"""
        with patch('utils.Color_decoration_utils.avatars_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('utils.Color_decoration_utils.avatars_col.update_one', new_callable=AsyncMock), \
             patch('utils.Color_decoration_utils.COLOR_PALETTE', ["#FF0000", "#00FF00"]):
            
            color = await get_sender_avatar_color("new@example.com")
            assert color in ["#FF0000", "#00FF00"]
    
    @pytest.mark.asyncio
    async def test_assigns_new_color_if_no_char_color_field(self):
        """Test assigning new color when document exists but has no char_color"""
        mock_doc = {"email": "test@example.com"}  # No char_color field
        
        with patch('utils.Color_decoration_utils.avatars_col.find_one', new_callable=AsyncMock, return_value=mock_doc), \
             patch('utils.Color_decoration_utils.avatars_col.update_one', new_callable=AsyncMock), \
             patch('utils.Color_decoration_utils.COLOR_PALETTE', ["#FF0000"]):
            
            color = await get_sender_avatar_color("test@example.com")
            assert color == "#FF0000"
    
    @pytest.mark.asyncio
    async def test_updates_database_with_new_color(self):
        """Test that new color is saved to database"""
        mock_update = AsyncMock()
        
        with patch('utils.Color_decoration_utils.avatars_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('utils.Color_decoration_utils.avatars_col.update_one', mock_update), \
             patch('utils.Color_decoration_utils.COLOR_PALETTE', ["#FF0000"]):
            
            await get_sender_avatar_color("new@example.com")
            mock_update.assert_called_once()
            
            # Check update_one was called with correct parameters
            call_args = mock_update.call_args
            assert call_args[0][0] == {"email": "new@example.com"}
            assert call_args[0][1]["$set"]["char_color"] == "#FF0000"
            assert call_args[1]["upsert"] is True
    
    @pytest.mark.asyncio
    async def test_different_senders_can_get_different_colors(self):
        """Test that different senders can be assigned different colors"""
        colors_assigned = []
        
        async def mock_find_one(query):
            return None
        
        async def mock_update_one(filter_doc, update_doc, **kwargs):
            colors_assigned.append(update_doc["$set"]["char_color"])
        
        with patch('utils.Color_decoration_utils.avatars_col.find_one', mock_find_one), \
             patch('utils.Color_decoration_utils.avatars_col.update_one', mock_update_one), \
             patch('utils.Color_decoration_utils.COLOR_PALETTE', ["#FF0000", "#00FF00", "#0000FF"]):
            
            await get_sender_avatar_color("sender1@example.com")
            await get_sender_avatar_color("sender2@example.com")
            
            assert len(colors_assigned) == 2
            # Colors should be from the palette
            for color in colors_assigned:
                assert color in ["#FF0000", "#00FF00", "#0000FF"]


class TestColorUtilsEdgeCases:
    """Test edge cases for color utilities"""
    
    @pytest.mark.asyncio
    async def test_empty_email_address(self):
        """Test with empty email address"""
        with patch('utils.Color_decoration_utils.avatars_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('utils.Color_decoration_utils.avatars_col.update_one', new_callable=AsyncMock), \
             patch('utils.Color_decoration_utils.COLOR_PALETTE', ["#FF0000"]):
            
            color = await get_sender_avatar_color("")
            assert color == "#FF0000"
    
    @pytest.mark.asyncio
    async def test_special_characters_in_email(self):
        """Test with special characters in email"""
        with patch('utils.Color_decoration_utils.avatars_col.find_one', new_callable=AsyncMock, return_value=None), \
             patch('utils.Color_decoration_utils.avatars_col.update_one', new_callable=AsyncMock), \
             patch('utils.Color_decoration_utils.COLOR_PALETTE', ["#FF0000"]):
            
            color = await get_sender_avatar_color("test+tag@example.com")
            assert color == "#FF0000"
