from unittest.mock import MagicMock, patch

import pytest
from instagrapi.exceptions import RateLimitError

from discord_insta.instagram_client import InstagramManager


@pytest.fixture
def mock_config():
    with patch("discord_insta.instagram_client.config") as mock:
        mock.ig_username = "testuser"
        mock.ig_password = "testpassword"
        mock.ig_thread_id = 1111
        mock.session_file = "test_session.json"
        yield mock

@pytest.fixture
def ig_manager(mock_config):
    with patch("instagrapi.Client") as mock_client_cls:
        manager = InstagramManager()
        manager.cl = mock_client_cls.return_value
        manager._bot_user_id = 123
        yield manager

def test_fetch_recent_messages_ignores_self(ig_manager):
    mock_msg1 = MagicMock()
    mock_msg1.user_id = 123  # Same as bot
    
    mock_msg2 = MagicMock()
    mock_msg2.user_id = 456  # Different user
    
    ig_manager.cl.direct_messages.return_value = [mock_msg1, mock_msg2]
    
    messages = ig_manager.fetch_recent_messages(limit=2)
    assert len(messages) == 1
    assert messages[0].user_id == 456

def test_fetch_recent_messages_rate_limit(ig_manager):
    ig_manager.cl.direct_messages.side_effect = RateLimitError("Too many requests")
    
    with patch("discord_insta.instagram_client.time.sleep") as mock_sleep:
        messages = ig_manager.fetch_recent_messages()
        
        assert len(messages) == 0
        mock_sleep.assert_called_once_with(60)

def test_get_username_caching(ig_manager):
    # Set up mock to return a username
    mock_user_info = MagicMock()
    mock_user_info.username = "real_user"
    ig_manager.cl.user_info.return_value = mock_user_info
    
    # First call should hit the API
    username = ig_manager.get_username("456")
    assert username == "real_user"
    ig_manager.cl.user_info.assert_called_once_with("456")
    
    # Reset mock and call again
    ig_manager.cl.user_info.reset_mock()
    
    username2 = ig_manager.get_username("456")
    assert username2 == "real_user"
    ig_manager.cl.user_info.assert_not_called()  # Should hit cache

def test_send_message(ig_manager, mock_config):
    ig_manager.send_message("Test send")
    ig_manager.cl.direct_send.assert_called_once_with(text="Test send", thread_ids=[1111])
