"""
Central configuration. All secrets come from environment variables —
never hardcode keys here. Copy .env.example to .env and fill in real
values (or set these as env vars on Render).
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Supabase ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""  # server-side key, never exposed to CLI

    # --- Paddle ---
    paddle_api_key: str = ""
    paddle_webhook_secret: str = ""
    paddle_env: str = "sandbox"  # "sandbox" or "production"

    # --- Provider API keys (yours — you hold these, not the customer) ---
    vast_api_key: str = ""
    runpod_api_key: str = ""
    lambda_api_key: str = ""
    crusoe_access_key: str = ""
    crusoe_secret_key: str = ""
    crusoe_project_id: str = ""
    digitalocean_token: str = ""

    # --- Pricing ---
    # Fraction of live cost added as your margin, e.g. 0.30 = cost * 1.30
    default_margin: float = 0.30
    # Absolute minimum margin per GPU-hour in USD, protects against
    # razor-thin spreads on already-cheap cards.
    min_margin_usd_per_hr: float = 0.03

    # --- Benchmark thresholds ---
    # Minimum fraction of a GPU model's expected throughput to accept
    # an instance. Below this, we treat it as throttled/misrepresented
    # and fall back to the next candidate.
    benchmark_min_ratio: float = 0.80

    class Config:
        env_file = ".env"


settings = Settings()
