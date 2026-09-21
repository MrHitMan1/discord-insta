from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ig_username: str
    ig_password: str
    ig_thread_id: int
    
    discord_token: str
    discord_channel_id: int
    
    # Optional settings with defaults
    poll_interval_seconds: int = 300
    session_file: str = "session.json"
    last_message_file: str = "last_message.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

config = Settings()
