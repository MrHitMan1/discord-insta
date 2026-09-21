import os

# Set dummy environment variables for tests so tests can run cleanly without a .env file
os.environ.setdefault("IG_USERNAME", "test_burner_user")
os.environ.setdefault("IG_PASSWORD", "test_burner_pass")
os.environ.setdefault("IG_THREAD_ID", "123456789")
os.environ.setdefault("DISCORD_TOKEN", "test_discord_token")
os.environ.setdefault("DISCORD_CHANNEL_ID", "987654321")
