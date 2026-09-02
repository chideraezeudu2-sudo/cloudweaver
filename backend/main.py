"""
FastAPI backend. This is the entire server surface the CLI talks to --
deliberately no HTML/frontend routes here. Deploy this to Render (matches
your existing stack) as a standard web service.

Run locally: uvicorn main:app --reload
"""

from __future__ import annotations

import asyncio
import logging
import os
import urllib.request
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import stripe
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel

from core import db, wallet
from core.broker import NoCapacityAvailable, quote_and_reserve
from core.metering import meter_once

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gpu-broker")

# In-app metering loop (BUILD_SPEC §5, free-tier variant). Because Render's
# free web services spin down after 15 min of no inbound traffic, we:
#   1. run meter_once() every 5 minutes in a background task, and
#   2. self-ping /health every 4 minutes so the container never hits
#      the idle spin-down in the normal case.
# After a Render restart/cold-start the first pass catches up the whole
# elapsed interval from last_metered_at (no double-bill, worst case ~5 min
# extra unmetered after a crash -- a rounding error at these prices, per spec.
METER_INTERVAL_SECONDS = 300
KEEPALIVE_INTERVAL_SECONDS = 240


async def _meter_loop():
    while True:
        try:
            await asyncio.to_thread(meter_once)
        except Exception:  # noqa: BLE001
            logger.exception("metering pass failed -- will retry next interval")
        await asyncio.sleep(METER_INTERVAL_SECONDS)


async def _keepalive_loop():
    while True:
        await asyncio.sleep(KEEPALIVE_INTERVAL_SECONDS)
        try:
            urllib.request.urlopen("http://127.0.0.1/health", timeout=10)
        except Exception:  # noqa: BLE001
            logger.warning("self-health ping failed", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(_meter_loop()),
        asyncio.create_task(_keepalive_loop()),
    ]
    logger.info("metering loop started (every %ss;keepalive every %ss)",
                 METER_INTERVAL_SECONDS, KEEPALIVE_INTERVAL_SECONDS)
    try:
        yield
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="GPU Broker API", lifespan=lifespan)

# Path to a broker-owned SSH keypair used to access every instance we
# provision, across all providers -- generate this once during deploy
# setup (see BUILD_SPEC.md), not per-customer.
BROKER_SSH_PUBLIC_KEY = os.environ["BROKER_SSH_PUBLIC_KEY"]
BROKER_SSH_PRIVATE_KEY_PATH = os.environ["BROKER_SSH_PRIVATE_KEY_PATH"]


@app.get("/health")
def health() -> dict:
    """Health: also used by the in-app keepalive loop."""
    return {"status": "ok", "service": "gpu-broker-api"}


@app.get("/")
def root() -> dict:
    """Health check: Render probes this path to decide the deploy is live."""
    return {"status": "ok", "service": "gpu-broker-api"}


def get_user_id(authorization: str = Header(...)) -> str:
    """Auth: the CLI sends `Authorization: Bearer <api_key>`. We hash the
    token and look it up against `users.api_key_hash` in Supabase.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "missing bearer token")
    token = authorization.removeprefix("Bearer ")
    try:
        return db.get_user_id_by_api_key(token)
    except KeyError:
        raise HTTPException(401, "unknown api key")


class SignupRequest(BaseModel):
    email: str


@app.post("/signup")
def signup(req: SignupRequest) -> dict:
    """Create a users row + wallet, and return a one-time API key.

    The raw key is returned exactly once here; only its SHA-256 hash is
    stored (see BUILD_SPEC.md §3).
    """
    email = (req.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(400, "invalid email")
    user_id, raw_key = db.create_user_with_api_key(email)
    return {
        "user_id": user_id,
        "api_key": raw_key,
        "note": "Save this key now -- it is shown once and cannot be "
                "recovered. Only its hash is stored.",
    }


class AddFundsRequest(BaseModel):
    amount_usd: float


@app.post("/wallet/add-funds")
def add_funds(req: AddFundsRequest, user_id: str = Depends(get_user_id)):
    if req.amount_usd < 5:
        raise HTTPException(400, "minimum top-up is $5")
    url = wallet.create_checkout_session(user_id, req.amount_usd)
    return {"checkout_url": url}


@app.get("/wallet/balance")
def balance(user_id: str = Depends(get_user_id)):
    return {"balance_usd": wallet.get_balance(user_id)}


@app.post("/stripe/webhook")
async def stripe_webhook(request: Request,
                          stripe_signature: str = Header(None)):
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, os.environ["STRIPE_WEBHOOK_SECRET"])
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(400, f"invalid webhook: {e}") from e

    if event["type"] == "checkout.session.completed":
        wallet.handle_checkout_completed_webhook(event)
    return {"received": True}


class RunJobRequest(BaseModel):
    gpu_model: str
    num_gpus: int = 1
    image: str = "pytorch/pytorch"
    max_hours: float = 4.0  # used to estimate the balance check up front


@app.post("/jobs/run")
def run_job(req: RunJobRequest, background_tasks: BackgroundTasks,
            user_id: str = Depends(get_user_id)):
    """
    Synchronously does the probe/reserve/benchmark dance (this can take
    30-90s -- the CLI should show a spinner, not treat this as instant).
    Metering happens in a background loop kicked off here; see
    BUILD_SPEC.md for why that's a background job/cron rather than
    something triggered by this single request.
    """
    # Rough ceiling estimate before we even know the real price, using the
    # highest plausible per-hour rate across providers for this GPU model.
    estimated_ceiling = req.max_hours * 3.0 * req.num_gpus
    try:
        wallet.reserve_for_job(user_id, estimated_ceiling)
    except wallet.InsufficientBalance as e:
        raise HTTPException(402, str(e)) from e

    try:
        result = quote_and_reserve(
            gpu_model=req.gpu_model,
            num_gpus=req.num_gpus,
            ssh_public_key=BROKER_SSH_PUBLIC_KEY,
            ssh_private_key_path=BROKER_SSH_PRIVATE_KEY_PATH,
            image=req.image,
        )
    except NoCapacityAvailable as e:
        raise HTTPException(503, str(e)) from e

    job_id = str(uuid.uuid4())
    # Persist the job row so the metering loop (Render cron, every 5 min)
    # can find it. Only after quote_and_reserve() returns a verified
    # instance -- never before (see wallet.refund_unbilled()).
    db.insert_job(
        job_id=job_id,
        user_id=user_id,
        provider=result.offer.provider,
        provider_instance_id=result.instance.instance_id,
        gpu_model=req.gpu_model,
        price_per_hour=result.customer_price_per_hour,
        provider_cost_per_hour=result.offer.price_per_hour,
        benchmark_power_watts=result.benchmark_power_watts,
        benchmark_tflops=result.benchmark_tflops,
        max_hours=req.max_hours,
    )

    return {
        "job_id": job_id,
        "provider": result.offer.provider,
        "instance_id": result.instance.instance_id,
        "ssh_host": result.instance.ssh_host,
        "price_per_hour": result.customer_price_per_hour,
        "benchmark": {
            "power_watts": result.benchmark_power_watts,
            "tflops": result.benchmark_tflops,
        },
    }


@app.get("/jobs")
def list_jobs(user_id: str = Depends(get_user_id)):
    return {"jobs": db.list_jobs_for_user(user_id)}
