"""Application configuration, loaded from environment variables / .env file.

Uses pydantic-settings so every value is validated and type-hinted, with
sensible defaults for local development wherever it is safe to have one.

V1.5: Added AI Gateway configuration (key pools, models, routing, health).
All gateway fields have safe defaults so existing .env files continue to work.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: str) -> list[str]:
    """Parse a comma-separated string into a stripped, non-empty list."""
    return [item.strip() for item in value.split(",") if item.strip()]


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

    # ── Telegram ──────────────────────────────────────────────────────── #
    bot_token: str

    # ── Database ──────────────────────────────────────────────────────── #
    database_url: str = "sqlite+aiosqlite:///./memorabot.db"

    # ── AI Provider (legacy single-provider mode) ─────────────────────── #
    # Set AI_PROVIDER=gateway to activate the full AI Gateway.
    # Set AI_PROVIDER=gemini or AI_PROVIDER=groq for single-provider mode
    # (backward-compatible, uses gemini_api_key / groq_api_key directly).
    ai_provider: str = "gateway"          # "gateway" | "gemini" | "groq" | "mock"
    gemini_api_key: str = ""              # used in legacy single-provider mode
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""               # used in legacy single-provider mode
    groq_model: str = "llama-3.3-70b-versatile"
    mnemonic_prompt_version: str = "v1"  # which app/knowledge/<x>/ to use

    # ── AI Gateway — Key Pools ────────────────────────────────────────── #
    # Each field is a comma-separated list of API keys.
    # Supports up to N keys per provider/tier (no hardcoded limit).
    # Example: FREE_GEMINI_KEYS=key1,key2,key3
    free_gemini_keys: str = ""    # FREE  pool: Gemini API keys
    premium_gemini_keys: str = "" # PREMIUM pool: Gemini API keys
    free_groq_keys: str = ""      # FREE  pool: Groq API keys
    premium_groq_keys: str = ""   # PREMIUM pool: Groq API keys

    # ── AI Gateway — Models ───────────────────────────────────────────── #
    # Comma-separated; tried in order (first model is primary, rest are fallbacks).
    gemini_models: str = "gemini-2.5-flash,gemini-2.5-flash-lite"
    groq_models: str = "llama-3.3-70b-versatile,qwen-qwq-32b,deepseek-r1-distill-llama-70b"

    # ── AI Gateway — Routing & Health ─────────────────────────────────── #
    # Comma-separated provider names in priority order (first = primary).
    gateway_provider_priority: str = "gemini,groq"
    # Seconds a key stays on cooldown after a provider-level failure (503/timeout).
    gateway_recovery_seconds: float = 300.0
    # Consecutive failures before a key is automatically put on cooldown.
    gateway_failure_threshold: int = 3
    # HTTP timeout per individual request (seconds).
    gateway_request_timeout: float = 30.0
    # How many times to retry a transient error before rotating to the next key.
    gateway_retry_count: int = 1
    # Load balancing strategy (only "round_robin" is implemented; reserved for future).
    gateway_load_balancer: str = "round_robin"

    # ── Free plan (see docs/MNEMONIC_LIBRARY.md) ──────────────────────── #
    # Cached words never consume this — only genuinely new AI calls count.
    free_plan_generation_limit: int = 3    # V1.2 legacy — kept for .env compat
    free_plan_daily_generations: int = 3   # V1.3 rolling daily quota for free users

    # ── Logging ───────────────────────────────────────────────────────── #
    log_level: str = "INFO"

    # ── Quiz ──────────────────────────────────────────────────────────── #
    # Telegram poll open_period in seconds (15–20 s is the recommended range).
    # Set QUIZ_OPEN_PERIOD=0 to disable the timer (polls stay open until answered).
    quiz_open_period: int = 20

    # Grammar channel — the Telegram channel that stores grammar lesson messages.
    # Set GRAMMAR_CHANNEL_ID=-100xxxxxxxxxx in .env (negative for supergroups/channels).
    # 0 means "not configured" — the bot will show a clean error to the user.
    grammar_channel_id: int = 0

    # Grammar quiz configuration.
    # GRAMMAR_QUIZ_QUESTIONS — number of questions per grammar quiz session.
    # GRAMMAR_QUIZ_TIME_SECONDS — Telegram poll open_period in seconds.
    # Both are clamped in GrammarService / the handler.
    grammar_quiz_questions: int = 5
    grammar_quiz_time_seconds: int = 20

    # Number of questions generated for a Vocabulary quiz.
    # Clamped to [2, 10] in QuizService.  Auto-reduced if the user
    # has fewer saved words than this value — never fabricates questions.
    # Override with QUIZ_VOCABULARY_QUESTIONS=5 in .env.
    quiz_vocabulary_questions: int = 5

    # ── Broadcast ─────────────────────────────────────────────────────── #
    broadcast_delay_ms: int = 50

    # ── Admin Panel ───────────────────────────────────────────────────── #
    admin_ids: str = ""

    # ── Referral & Coin economy ───────────────────────────────────────── #
    referral_base_reward: int = 20
    referral_increment: int = 2
    referral_max_reward: int = 100
    premium_daily_cost: int = 100
    welcome_referral_bonus: int = 0
    top_referrers_limit: int = 10
    bot_username: str = "MemoraBot"

    # ── Derived / computed properties ─────────────────────────────────── #

    @property
    def admin_id_list(self) -> list[int]:
        """Parsed list of admin Telegram user IDs."""
        return [int(c.strip()) for c in self.admin_ids.split(",") if c.strip()]

    @property
    def free_gemini_key_list(self) -> list[str]:
        return _split_csv(self.free_gemini_keys)

    @property
    def premium_gemini_key_list(self) -> list[str]:
        return _split_csv(self.premium_gemini_keys)

    @property
    def free_groq_key_list(self) -> list[str]:
        return _split_csv(self.free_groq_keys)

    @property
    def premium_groq_key_list(self) -> list[str]:
        return _split_csv(self.premium_groq_keys)

    @property
    def gemini_model_list(self) -> list[str]:
        return _split_csv(self.gemini_models)

    @property
    def groq_model_list(self) -> list[str]:
        return _split_csv(self.groq_models)

    @property
    def gateway_provider_priority_list(self) -> list[str]:
        return _split_csv(self.gateway_provider_priority)


settings = Settings()
