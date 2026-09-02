"""Supabase data access + API-key auth helpers.

Auth model (BUILD_SPEC §3): each user gets a random 32-byte API key at
signup. Only a SHA-256 hash of that key is ever stored, in
`users.api_key_hash`. The raw key is shown to the user exactly once.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import uuid

from supabase import Client, create_client


def get_supabase() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"],
    )


def hash_api_key(raw_key: str) -> str:
    """Hash an API key for storage / lookup. Never store the raw key."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Random 32-byte API key. Returned to the user exactly once."""
    return secrets.token_urlsafe(32)


def create_user_with_api_key(email: str) -> tuple[str, str]:
    """Create a users row + wallet, return (user_id, raw_api_key).

    The raw key is returned exactly once here; only its hash is stored.
    """
    raw_key = generate_api_key()
    user_id = str(uuid.uuid4())
    db = get_supabase()

    db.table("users").insert({
        "id": user_id,
        "email": email,
        "api_key_hash": hash_api_key(raw_key),
    }).execute()
    db.table("wallets").insert({
        "user_id": user_id,
        "balance_usd": 0,
    }).execute()
    return user_id, raw_key


def get_user_id_by_api_key(raw_key: str) -> str:
    """Look up a user_id by raw API key. Raises KeyError if unknown."""
    db = get_supabase()
    result = db.table("users").select("id") \
        .eq("api_key_hash", hash_api_key(raw_key)).maybe_single().execute()
    if not result.data:
        raise KeyError("unknown api key")
    return result.data["id"]


def insert_job(job_id: str, user_id: str, provider: str,
               provider_instance_id: str, gpu_model: str,
               price_per_hour: float, provider_cost_per_hour: float,
               benchmark_power_watts: float | None,
               benchmark_tflops: float | None,
               max_hours: float = 4.0) -> None:
    db = get_supabase()
    db.table("jobs").insert({
        "id": job_id,
        "user_id": user_id,
        "provider": provider,
        "provider_instance_id": provider_instance_id,
        "gpu_model": gpu_model,
        "price_per_hour": price_per_hour,
        "provider_cost_per_hour": provider_cost_per_hour,
        "benchmark_power_watts": benchmark_power_watts,
        "benchmark_tflops": benchmark_tflops,
        "max_hours": max_hours,
        "status": "running",
    }).execute()


def list_jobs_for_user(user_id: str) -> list[dict]:
    db = get_supabase()
    result = db.table("jobs").select("*") \
        .eq("user_id", user_id).order("started_at", desc=True).execute()
    return result.data or []


def list_running_jobs() -> list[dict]:
    """All jobs with status='running' -- the metering loop's work queue."""
    db = get_supabase()
    result = db.table("jobs").select("*") \
        .eq("status", "running").execute()
    return result.data or []


def update_job_status(job_id: str, status: str,
                      ended_at: str | None = None) -> None:
    db = get_supabase()
    payload: dict = {"status": status}
    if ended_at:
        payload["ended_at"] = ended_at
    db.table("jobs").update(payload).eq("id", job_id).execute()
