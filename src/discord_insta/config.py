from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ig_username: str = ""
    ig_password: str = ""
    ig_thread_id: int = 0
    
    discord_token: str = ""
    discord_channel_id: int = 0
    
    # Optional settings with defaults
    poll_interval_seconds: int = 300
    session_file: str = "session.json"
    last_message_file: str = "last_message.json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def validate_required(self) -> None:
        missing = []
        if not self.ig_username:
            missing.append("IG_USERNAME")
        if not self.ig_password:
            missing.append("IG_PASSWORD")
        if not self.ig_thread_id:
            missing.append("IG_THREAD_ID")
        if not self.discord_token:
            missing.append("DISCORD_TOKEN")
        if not self.discord_channel_id:
            missing.append("DISCORD_CHANNEL_ID")
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}. "
                "Please configure them in your .env file or environment variables."
            )


config = Settings()
