from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import discord
import pytest

from discord_insta.discord_bot import DiscordInstaBot


@pytest.fixture
def mock_config():
    with patch("discord_insta.discord_bot.config") as mock:
        mock.discord_channel_id = 123456
        mock.discord_token = "dummy_token"
        mock.poll_interval_seconds = 300
        mock.last_message_file = "test_last_message.json"
        yield mock

@pytest.fixture
def bot(mock_config):
    # Mock bot initial state to prevent actual connections
    with patch("discord_insta.discord_bot.async_login"), \
         patch("discord_insta.discord_bot.os.path.exists", return_value=False):
        bot_instance = DiscordInstaBot()
        yield bot_instance

@pytest.mark.asyncio
async def test_on_message_ignores_self(bot):
    message = MagicMock(spec=discord.Message)
    message.author = bot.user
    
    with patch("discord_insta.discord_bot.async_send_message") as mock_send:
        await bot.on_message(message)
        mock_send.assert_not_called()

@pytest.mark.asyncio
async def test_on_message_forwards_to_instagram(bot, mock_config):
    message = MagicMock(spec=discord.Message)
    message.author.name = "TestUser"
    message.content = "Hello IG"
    message.author.__eq__.return_value = False # Not self
    message.channel.id = mock_config.discord_channel_id
    message.attachments = []
    
    with (
        patch("discord_insta.discord_bot.async_send_message", new_callable=AsyncMock) as mock_send,
        patch.object(type(bot), "user", new_callable=PropertyMock) as mock_user,
    ):
        mock_user.return_value = MagicMock(id=999)
        bot.process_commands = AsyncMock()
        await bot.on_message(message)
        mock_send.assert_called_once_with("TestUser: Hello IG")

@pytest.mark.asyncio
async def test_on_message_with_attachment(bot, mock_config):
    message = MagicMock(spec=discord.Message)
    message.author.name = "TestUser"
    message.content = "Look at this!"
    message.author.__eq__.return_value = False
    message.channel.id = mock_config.discord_channel_id
    
    attachment = MagicMock()
    attachment.url = "http://example.com/image.png"
    message.attachments = [attachment]
    
    with (
        patch("discord_insta.discord_bot.async_send_message", new_callable=AsyncMock) as mock_send,
        patch.object(type(bot), "user", new_callable=PropertyMock) as mock_user,
    ):
        mock_user.return_value = MagicMock(id=999)
        bot.process_commands = AsyncMock()
        await bot.on_message(message)
        mock_send.assert_called_once_with("TestUser: Look at this!\nhttp://example.com/image.png")
