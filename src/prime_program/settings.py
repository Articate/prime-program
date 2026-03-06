from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_key: str
    log_level: str = "INFO"
    elo_scale: int = 2000
    elo_k_factor: int = 20
    elite_bottom_cliff_top_rank: int = 600
    elite_bottom_cliff_max_rank: int = 900
    elite_bottom_cliff_top_points: int = 808
    elite_bottom_cliff_power: int = 2
    command_sync_guild_ids: list[int] = Field(default_factory=lambda: [1378169042514481245])


settings = Settings()  # type: ignore
