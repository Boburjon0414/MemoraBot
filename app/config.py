"""Application configuration, loaded from environment variables / .env file.

Uses pydantic-settings so every value is validated and type-hinted, with
sensible defaults for local development wherever it is safe to have one.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Fields are matched case-insensitively against environment variables /
    the `.env` file by default (e.g. `bot_token` <-> `BOT_TOKEN`).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Telegram -----------------------------------------------------
    bot_token: str

    # --- Database -------------------------------------------------------
    database_url: str = "sqlite+aiosqlite:///./memorabot.db"

    # --- AI provider ------------------------------------------------------
    ai_provider: str = "gemini"  # "gemini" | "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    mnemonic_prompt_version: str = "v1"  # which app/knowledge/<x>/ to use

    # --- Free plan (see docs/MNEMONIC_LIBRARY.md) --------------------------
    # Cached words never consume this — only a genuinely new word (a cache
    # miss, requiring a real Gemini call) counts against the limit.
    free_plan_generation_limit: int = 3

    # --- Logging ----------------------------------------------------------
    log_level: str = "INFO"

    # --- Reserved for the future Admin Panel (see README) ------------------
    admin_ids: str = ""

    @property
    def admin_id_list(self) -> list[int]:
        """Parsed list of admin Telegram user IDs from the comma-separated value."""
        return [int(chunk.strip()) for chunk in self.admin_ids.split(",") if chunk.strip()]


settings = Settings()
