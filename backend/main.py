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

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from paddle_billing.Notifications import Secret, Verifier
from pydantic import BaseModel

import legal_content

from core import db, wallet
from core.broker import NoCapacityAvailable, quote_and_reserve
from core.metering import meter_once

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloudweaver")

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


# NOTE: this default value is the ACTUAL live Render URL, not just a
# brand placeholder -- do not change it without also updating Paddle's
# webhook destination and default payment link to match, or checkout
# and webhook delivery will break. Cosmetic rebrand (Cloud Weaver) does
# NOT include renaming this yet -- see render.yaml's note on the same.
PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://gpu-broker-api.onrender.com")


async def _keepalive_loop():
    # IMPORTANT: this must hit the PUBLIC url, not localhost/127.0.0.1.
    # Render's spin-down timer only resets on inbound traffic that arrives
    # through its edge/router -- a loopback request from inside the same
    # container never leaves the box and does not count, so this would
    # silently fail to prevent spin-down if pointed at localhost.
    while True:
        await asyncio.sleep(KEEPALIVE_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(
                urllib.request.urlopen, f"{PUBLIC_URL}/health", None, 15)
        except Exception:  # noqa: BLE001
            logger.warning("self-health ping to %s failed", PUBLIC_URL,
                            exc_info=True)


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


app = FastAPI(title="Cloud Weaver API", lifespan=lifespan)

# Path to a broker-owned SSH keypair used to access every instance we
# provision, across all providers -- generate this once during deploy
# setup (see BUILD_SPEC.md), not per-customer.
BROKER_SSH_PUBLIC_KEY = os.environ["BROKER_SSH_PUBLIC_KEY"]
BROKER_SSH_PRIVATE_KEY_PATH = os.environ["BROKER_SSH_PRIVATE_KEY_PATH"]


@app.get("/health")
def health() -> dict:
    """Health: also used by the in-app keepalive loop."""
    return {"status": "ok", "service": "cloudweaver-api"}


@app.get("/")
def root() -> dict:
    """Health check: Render probes this path to decide the deploy is live."""
    return {"status": "ok", "service": "cloudweaver-api"}


PADDLE_CLIENT_TOKEN = os.environ.get("PADDLE_CLIENT_TOKEN", "")


@app.get("/about", response_class=HTMLResponse)
def about_page() -> str:
    """Product description page -- exists specifically so Paddle's live
    domain review has a real page to look at without needing a purchased
    domain. Deliberately NOT at '/' since Render's health check and the
    in-app keepalive both depend on that path returning the JSON status
    body, not HTML."""
    return legal_content.ABOUT_PAGE


@app.get("/terms", response_class=HTMLResponse)
def terms_page() -> str:
    return legal_content.TERMS_PAGE


@app.get("/privacy", response_class=HTMLResponse)
def privacy_page() -> str:
    return legal_content.PRIVACY_PAGE


@app.get("/pay", response_class=HTMLResponse)
def pay_page() -> str:
    """
    Paddle's default payment link (set in the Paddle dashboard's Checkout
    Settings) must point HERE, not at the bare API root -- Paddle appends
    `?_ptxn=txn_...` to whatever URL is configured there, and that page
    must load Paddle.js for a checkout to actually render. The API root
    only ever served JSON, which is why checkout URLs returned by
    /wallet/add-funds loaded a blank JSON blob instead of a payment form
    (found and diagnosed by OpenHands against Paddle's own documented
    default-payment-link behavior).

    Per Paddle's docs, Paddle.js auto-detects a `_ptxn` transaction id in
    the page's own URL and opens the checkout for it automatically once
    initialized -- this page does nothing but load and initialize
    Paddle.js; it doesn't need to read the query param itself. That
    auto-open behavior is documented but has not been exercised against
    a real browser here -- confirm it actually renders before trusting
    this as fully done, same as everything else flagged along the way.
    """
    if not PADDLE_CLIENT_TOKEN:
        return (
            "<h1>Checkout misconfigured</h1>"
            "<p>PADDLE_CLIENT_TOKEN is not set on the server. This is a "
            "different value than PADDLE_API_KEY -- generate a Client-side "
            "Token (not an API key) in the Paddle dashboard under "
            "Developer Tools &rarr; Authentication, and set it as an env "
            "var.</p>"
        )
    is_sandbox = os.environ.get("PADDLE_ENV", "sandbox") == "sandbox"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Complete your payment</title></head>
<body>
  <p>Loading checkout&hellip;</p>
  <script src="https://cdn.paddle.com/paddle/v2/paddle.js"></script>
  <script>
    {"Paddle.Environment.set('sandbox');" if is_sandbox else ""}
    Paddle.Initialize({{ token: "{PADDLE_CLIENT_TOKEN}" }});
    // Paddle.js reads `_ptxn` from this page's own URL automatically and
    // opens the matching checkout once initialized -- no manual call
    // needed here per Paddle's documented default-payment-link behavior.
  </script>
</body>
</html>"""


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
    # Paddle's catalog model wants one of the pre-defined tiers, not a
    # freeform typed-in amount -- see wallet.PADDLE_PRICE_IDS.
    tier_usd: int


@app.post("/wallet/add-funds")
def add_funds(req: AddFundsRequest, user_id: str = Depends(get_user_id)):
    try:
        url = wallet.create_checkout_session(user_id, req.tier_usd)
    except wallet.InvalidTier as e:
        raise HTTPException(400, str(e)) from e
    return {"checkout_url": url}


@app.get("/wallet/balance")
def balance(user_id: str = Depends(get_user_id)):
    return {"balance_usd": wallet.get_balance(user_id)}


_paddle_webhook_verifier = Verifier()


class _PaddleWebhookRequest:
    """Adapter satisfying paddle_billing's Request protocol (needs .body
    as bytes and .headers with a .get(key, default) method). FastAPI's
    own Request exposes body only via an async method, and Starlette's
    Headers already implements .get() -- confirmed both against the
    installed SDK's actual Protocol definitions, not guessed."""
    def __init__(self, body: bytes, headers) -> None:
        self.body = body
        self.content = body
        self.data = body
        self.headers = headers


@app.post("/paddle/webhook")
async def paddle_webhook(request: Request):
    raw_body = await request.body()
    wrapped_request = _PaddleWebhookRequest(raw_body, request.headers)
    secret = Secret(os.environ["PADDLE_WEBHOOK_SECRET"])

    try:
        is_valid = _paddle_webhook_verifier.verify(wrapped_request, secret)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"webhook verification error: {e}") from e
    if not is_valid:
        raise HTTPException(400, "invalid Paddle webhook signature")

    import json
    payload = json.loads(raw_body)
    if payload.get("event_type") == "transaction.completed":
        wallet.handle_transaction_completed_webhook(payload)
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
