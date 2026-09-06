"""
Wallet: Stripe holds and moves money, Supabase holds the balance and the
ledger of what happened. Nobody gets charged per-job on their card directly
-- the balance is decremented from a prepaid wallet instead (fees, latency,
declined-card-mid-job risk are why).

HISTORY: this was Stripe originally, swapped to Paddle, then swapped back
to Stripe after Paddle's live account got stuck in review and a separate
Stripe attempt hit a 30-day restriction on a first account. This is a
SECOND Stripe account (opened specifically for Cloud Weaver by a
cofounder) -- if this one also gets restricted, that's a real signal
worth escalating rather than trying a third processor blind.

Unlike Paddle, Stripe supports true off-session auto-reload for a
one-off top-up (this is what OpenRouter's auto-recharge actually uses)
-- restored below as _maybe_auto_reload, gated behind an explicit
opt-in per user (auto_reload_enabled) rather than always-on.

This module deliberately does NOT build a dashboard -- every one of these
functions is meant to be called from the CLI (see cli/cloudweaver_cli/cli.py)
or the backend's own job-metering loop, never from a webpage.
"""

from __future__ import annotations

import logging
import os

import stripe
from supabase import Client as SupabaseClient, create_client

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

_supabase: SupabaseClient = create_client(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

logger = logging.getLogger("wallet")


class InsufficientBalance(Exception):
    pass


def create_checkout_session(user_id: str, amount_usd: float) -> str:
    """Returns a hosted Stripe Checkout URL. The CLI just prints this link
    -- Stripe builds and hosts the actual payment page, we build nothing.
    Also collects a card on file for auto-reload (see _maybe_auto_reload
    below), since Checkout in `setup_future_usage` mode can save a
    payment method for later off-session use.

    Unlike Paddle, Stripe allows a freeform typed-in amount rather than
    pre-defined catalog tiers -- kept a $5 minimum as a sane floor.
    """
    if amount_usd < 5:
        raise ValueError("minimum top-up is $5")

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Cloud Weaver credits"},
                "unit_amount": int(amount_usd * 100),
            },
            "quantity": 1,
        }],
        payment_intent_data={"setup_future_usage": "off_session"},
        client_reference_id=user_id,
        success_url=f"{os.environ.get('PUBLIC_URL', '')}/pay/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{os.environ.get('PUBLIC_URL', '')}/pay/cancelled",
    )
    return session.url


def handle_checkout_completed_webhook(event: dict) -> None:
    """Call this from your Stripe webhook endpoint (see main.py). Credits
    the wallet ONLY on confirmed payment, never on the client just saying
    'I paid' -- that trust boundary matters.

    Idempotent the same way the Paddle version was: credit_wallet's
    unique index on stripe_session_id means a Stripe webhook retry
    (Stripe retries failed deliveries the same way Paddle does) is a
    safe no-op, not a double credit -- this was fixed at the database
    level, so it protects either payment processor automatically.
    """
    session = event["data"]["object"]
    user_id = session.get("client_reference_id")
    if not user_id:
        logger.warning(
            "checkout session %s has no client_reference_id -- ignoring",
            session.get("id"),
        )
        return

    amount_usd = session["amount_total"] / 100

    payment_method_id = None
    if session.get("payment_intent"):
        intent = stripe.PaymentIntent.retrieve(session["payment_intent"])
        payment_method_id = intent.get("payment_method")

    _supabase.rpc("credit_wallet", {
        "p_user_id": user_id,
        "p_amount": amount_usd,
        "p_stripe_session_id": session["id"],
    }).execute()

    if payment_method_id:
        _supabase.table("users").update({
            "stripe_payment_method_id": payment_method_id,
            "stripe_customer_id": session.get("customer"),
        }).eq("id", user_id).execute()


def get_balance(user_id: str) -> float:
    result = _supabase.table("wallets").select("balance_usd") \
        .eq("user_id", user_id).single().execute()
    return float(result.data["balance_usd"])


def reserve_for_job(user_id: str, estimated_max_cost_usd: float) -> None:
    """Call BEFORE reserving any GPU instance -- refuse to even attempt a
    reservation if the customer's balance can't cover a reasonable minimum
    run. Tries one auto-reload attempt first if the customer has opted in
    and has a card on file.
    """
    balance = get_balance(user_id)
    if balance < estimated_max_cost_usd:
        if not _maybe_auto_reload(user_id):
            raise InsufficientBalance(
                f"balance ${balance:.2f} insufficient for estimated "
                f"${estimated_max_cost_usd:.2f} -- run `cloudweaver add-funds`"
            )


# How far into the negative a job may run before it's force-terminated,
# if auto-reload isn't enabled or fails (e.g. card declined). This trades
# a small, bounded bad-debt risk for not killing a job that's almost
# finished right as the wallet crosses exactly $0.
GRACE_BUFFER_USD = 2.0

# When projected remaining runway (at current burn rate) drops below this
# many seconds, meter_job_usage flags a warning the caller should surface
# to the customer (CLI output / email) with a fresh top-up link -- kept
# as defense-in-depth even with auto-reload restored, since auto-reload
# can still fail (declined card, opted out).
LOW_BALANCE_WARNING_SECONDS = 20 * 60


class LowBalanceWarning(Exception):
    """Not a failure -- raised alongside a successful debit to signal the
    caller (main.py / core/metering.py) should surface a top-up nudge.
    Carries the projected minutes of runway left."""
    def __init__(self, minutes_remaining: float):
        self.minutes_remaining = minutes_remaining
        super().__init__(f"~{minutes_remaining:.0f} min of balance remaining")


def meter_job_usage(user_id: str, job_id: str, seconds_elapsed: int,
                     price_per_hour: float) -> None:
    """Call this periodically (e.g. every 5 minutes) while a job runs, NOT
    once at the end -- so a job that runs out of balance gets caught and
    stopped mid-flight rather than accumulating unbounded debt.

    Tries auto-reload before falling back to the grace buffer, then
    raises InsufficientBalance only if both fail.
    """
    cost = (seconds_elapsed / 3600) * price_per_hour
    balance = get_balance(user_id)

    if balance - cost < -GRACE_BUFFER_USD:
        if not _maybe_auto_reload(user_id):
            raise InsufficientBalance(
                f"job {job_id} balance depleted mid-run (${balance:.2f}, "
                f"grace buffer ${GRACE_BUFFER_USD:.2f} exhausted) -- caller "
                f"must terminate the instance"
            )
        balance = get_balance(user_id)

    _supabase.rpc("debit_wallet", {
        "p_user_id": user_id,
        "p_amount": cost,
        "p_job_id": job_id,
    }).execute()

    remaining_after = balance - cost
    if price_per_hour > 0:
        seconds_remaining = max(remaining_after, 0) / price_per_hour * 3600
        if seconds_remaining < LOW_BALANCE_WARNING_SECONDS:
            raise LowBalanceWarning(seconds_remaining / 60)


def refund_unbilled(job_id: str) -> None:
    """Call this when the broker's fallback logic destroys an instance for
    ghost inventory or a failed benchmark -- that time was never actually
    delivered to the customer, so it should never have been billed in the
    first place. In practice this means: only call meter_job_usage() AFTER
    core/broker.py's quote_and_reserve() has returned a verified instance,
    never before or during the probe/benchmark steps.
    """
    pass  # no-op placeholder: exists to document the invariant above


AUTO_RELOAD_THRESHOLD_USD = 5.0
AUTO_RELOAD_AMOUNT_USD = 20.0


def _maybe_auto_reload(user_id: str) -> bool:
    """True, silent, off-session auto-recharge -- the OpenRouter pattern.
    Only fires if the user opted in AND has a card on file from a
    previous checkout (see create_checkout_session's setup_future_usage).
    """
    user = _supabase.table("users").select(
        "stripe_customer_id, stripe_payment_method_id, auto_reload_enabled"
    ).eq("id", user_id).single().execute().data

    if not user or not user.get("auto_reload_enabled"):
        return False
    if not user.get("stripe_payment_method_id"):
        return False

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(AUTO_RELOAD_AMOUNT_USD * 100),
            currency="usd",
            customer=user["stripe_customer_id"],
            payment_method=user["stripe_payment_method_id"],
            off_session=True,
            confirm=True,
        )
    except stripe.error.CardError:
        # Card declined -- disable auto-reload rather than retry silently
        # forever; the customer needs to know and update their card.
        _supabase.table("users").update(
            {"auto_reload_enabled": False}
        ).eq("id", user_id).execute()
        return False

    if intent.status == "succeeded":
        _supabase.rpc("credit_wallet", {
            "p_user_id": user_id,
            "p_amount": AUTO_RELOAD_AMOUNT_USD,
            "p_stripe_session_id": intent.id,
        }).execute()
        return True
    return False
