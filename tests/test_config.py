import pytest

from discord_insta.config import Settings


def test_validate_required_raises_when_empty():
    settings = Settings(
        ig_username="",
        ig_password="",
        ig_thread_id=0,
        discord_token="",
        discord_channel_id=0,
    )
    with pytest.raises(ValueError, match="Missing required configuration"):
        settings.validate_required()


def test_validate_required_passes_when_set():
    settings = Settings(
        ig_username="valid_user",
        ig_password="valid_password",
        ig_thread_id=12345,
        discord_token="valid_token",
        discord_channel_id=67890,
    )
    # Should not raise
    settings.validate_required()
