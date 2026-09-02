"""
Wallet: Stripe holds and moves money, Supabase holds the balance and the
ledger of what happened. Nobody gets charged per-job on their card directly
-- see the conversation this spec came from for why (fees, latency,
declined-card-mid-job risk).

This module deliberately does NOT build a dashboard -- every one of these
functions is meant to be called from the CLI (see cli/gpu_deploy_cli/cli.py)
or the backend's own job-metering loop, never from a webpage.
"""

from __future__ import annotations

import os

import stripe
from supabase import Client, create_client

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

_supabase: Client = create_client(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)


class InsufficientBalance(Exception):
    pass


def create_checkout_session(user_id: str, amount_usd: float) -> str:
    """Returns a hosted Stripe Checkout URL. The CLI just prints this link
    -- Stripe builds and hosts the actual payment page, we build nothing.
    Also collects a card on file for auto-reload (see maybe_auto_reload
    below), since Checkout in `setup` mode can save a payment method.
    """
    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "GPU broker credits"},
                "unit_amount": int(amount_usd * 100),
            },
            "quantity": 1,
        }],
        # Saves the card for future off-session auto-reload charges.
        payment_intent_data={"setup_future_usage": "off_session"},
        client_reference_id=user_id,
        success_url="https://yourbroker.dev/funded?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://yourbroker.dev/cancelled",
    )
    return session.url


def handle_checkout_completed_webhook(event: dict) -> None:
    """Call this from your Stripe webhook endpoint (see main.py). Credits
    the wallet ONLY on confirmed payment, never on the client just saying
    'I paid' -- that trust boundary matters.
    """
    session = event["data"]["object"]
    user_id = session["client_reference_id"]
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
    run (see BUILD_SPEC.md for how estimated_max_cost_usd should be
    computed from the customer's requested max runtime)."""
    balance = get_balance(user_id)
    if balance < estimated_max_cost_usd:
        # Try one auto-reload attempt before giving up, if the user has
        # a card on file and auto-reload enabled.
        if not _maybe_auto_reload(user_id):
            raise InsufficientBalance(
                f"balance ${balance:.2f} insufficient for estimated "
                f"${estimated_max_cost_usd:.2f}"
            )


def meter_job_usage(user_id: str, job_id: str, seconds_elapsed: int,
                     price_per_hour: float) -> None:
    """Call this periodically (e.g. every 5 minutes) while a job runs, NOT
    once at the end -- so a job that runs out of balance gets caught and
    stopped mid-flight rather than accumulating a debt.
    """
    cost = (seconds_elapsed / 3600) * price_per_hour
    balance = get_balance(user_id)

    if balance < cost:
        if not _maybe_auto_reload(user_id):
            raise InsufficientBalance(
                f"job {job_id} balance depleted mid-run -- caller must "
                f"terminate the instance"
            )
        balance = get_balance(user_id)

    _supabase.rpc("debit_wallet", {
        "p_user_id": user_id,
        "p_amount": cost,
        "p_job_id": job_id,
    }).execute()


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
