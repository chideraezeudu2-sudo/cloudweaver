"""
Wallet: Paddle holds and moves money, Supabase holds the balance and the
ledger of what happened. Nobody gets charged per-job on their card directly
-- the balance is decremented from a prepaid wallet instead (fees, latency,
declined-card-mid-job risk are why).

PADDLE VS STRIPE NOTE: Paddle (as a merchant of record) does not support
charging a saved card off-session for a standalone one-off top-up the way
Stripe does -- confirmed against Paddle's docs, that pattern only exists
scoped to a subscription. So true silent auto-reload (what OpenRouter does
via Stripe) isn't available here. We compensate with: (1) a pre-flight
balance check before any job starts, (2) a proactive low-balance warning
during metering with a fresh top-up link, and (3) a small grace buffer
instead of an instant hard kill at exactly $0. See meter_job_usage below.

Paddle also expects pre-defined catalog Prices rather than a freeform
dollar amount -- PADDLE_PRICE_IDS below maps our fixed top-up tiers to
the Price IDs created in the Paddle dashboard (sandbox first).

This module deliberately does NOT build a dashboard -- every one of these
functions is meant to be called from the CLI (see cli/gpu_deploy_cli/cli.py)
or the backend's own job-metering loop, never from a webpage.
"""

from __future__ import annotations

import logging
import os

from paddle_billing import Client, Environment, Options
from paddle_billing.Entities.Shared.CustomData import CustomData
from paddle_billing.Resources.Transactions.Operations import CreateTransaction
from paddle_billing.Resources.Transactions.Operations.Create.TransactionCreateItem import (
    TransactionCreateItem,
)
from supabase import Client as SupabaseClient, create_client

_environment = (Environment.SANDBOX
                if os.environ.get("PADDLE_ENV", "sandbox") == "sandbox"
                else Environment.PRODUCTION)
_paddle = Client(os.environ["PADDLE_API_KEY"],
                  options=Options(_environment))

# Fixed top-up tiers -- Paddle's catalog model wants pre-defined Prices,
# not an arbitrary typed-in dollar amount like Stripe allowed. Create
# these once in the Paddle dashboard (sandbox first) and set the env vars.
PADDLE_PRICE_IDS: dict[int, str] = {
    5: os.environ.get("PADDLE_PRICE_ID_5", ""),
    10: os.environ.get("PADDLE_PRICE_ID_10", ""),
    20: os.environ.get("PADDLE_PRICE_ID_20", ""),
    50: os.environ.get("PADDLE_PRICE_ID_50", ""),
    100: os.environ.get("PADDLE_PRICE_ID_100", ""),
}

_supabase: SupabaseClient = create_client(
    os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)


class InsufficientBalance(Exception):
    pass


class InvalidTier(Exception):
    pass


def create_checkout_session(user_id: str, tier_usd: int) -> str:
    """Returns a hosted Paddle checkout URL for one of the fixed top-up
    tiers. The CLI just prints this link -- Paddle builds and hosts the
    actual payment page, we build nothing.
    """
    price_id = PADDLE_PRICE_IDS.get(tier_usd)
    if not price_id:
        raise InvalidTier(
            f"no Paddle price configured for ${tier_usd} -- valid tiers: "
            f"{sorted(k for k, v in PADDLE_PRICE_IDS.items() if v)}"
        )

    txn = _paddle.transactions.create(CreateTransaction(
        items=[TransactionCreateItem(price_id=price_id, quantity=1)],
        custom_data=CustomData({"user_id": user_id}),
    ))
    # Confirmed against the installed SDK's Transaction/Checkout entities
    # (not guessed): create() returns a Transaction whose .checkout is a
    # Checkout(url: str | None). Still worth confirming against one real
    # sandbox call that Paddle actually populates this url for a plain
    # transaction (vs. requiring an explicit checkout object on the
    # request) -- see BUILD_SPEC.md testing checklist.
    if not txn.checkout or not txn.checkout.url:
        raise RuntimeError(
            "Paddle did not return a checkout URL for this transaction -- "
            "may need an explicit `checkout` block on the create request"
        )
    return txn.checkout.url


logger = logging.getLogger("wallet")


def handle_transaction_completed_webhook(payload: dict) -> None:
    """Call this from your Paddle webhook endpoint (see main.py), AFTER
    verifying the Paddle-Signature header. Credits the wallet ONLY on a
    confirmed `transaction.completed` event, using grand_total (what the
    customer actually paid, including tax) -- never trust a client-side
    'I paid' signal.

    A transaction with no custom_data.user_id is logged and ignored, not
    raised -- confirmed against a real Paddle example payload that this
    field can legitimately be absent (e.g. a transaction that didn't
    originate from our own create_checkout_session call). Raising here
    would turn into a 500 on the webhook endpoint, and Paddle retries
    failed webhook deliveries -- for an event we can never resolve
    (no user_id to credit), that just retries forever for no benefit.
    """
    data = payload["data"]
    user_id = (data.get("custom_data") or {}).get("user_id")
    if not user_id:
        logger.warning(
            "transaction %s has no user_id in custom_data -- ignoring "
            "(not one of our checkout sessions, or a non-checkout event)",
            data.get("id"),
        )
        return

    grand_total_minor = int(data["details"]["totals"]["grand_total"])
    amount_usd = grand_total_minor / 100

    _supabase.rpc("credit_wallet", {
        "p_user_id": user_id,
        "p_amount": amount_usd,
        "p_stripe_session_id": data["id"],  # column name predates the Paddle swap, reused as-is
    }).execute()


def get_balance(user_id: str) -> float:
    result = _supabase.table("wallets").select("balance_usd") \
        .eq("user_id", user_id).single().execute()
    return float(result.data["balance_usd"])


def reserve_for_job(user_id: str, estimated_max_cost_usd: float) -> None:
    """Call BEFORE reserving any GPU instance -- refuse to even attempt a
    reservation if the customer's balance can't cover a reasonable minimum
    run. This is the primary defense against a job dying mid-run: if
    someone honestly states how long their job will run (--max-hours),
    they can't start something they can't afford to finish.

    No auto-reload attempt here (Paddle can't do off-session top-ups for
    a one-off purchase) -- this just raises, and the CLI tells the
    customer to run `cloudweaver add-funds` first.
    """
    balance = get_balance(user_id)
    if balance < estimated_max_cost_usd:
        raise InsufficientBalance(
            f"balance ${balance:.2f} insufficient for estimated "
            f"${estimated_max_cost_usd:.2f} -- run `cloudweaver add-funds`"
        )


# How far into the negative a job may run before it's force-terminated.
# This trades a small, bounded bad-debt risk for not killing a job that's
# almost finished right as the wallet crosses exactly $0.
GRACE_BUFFER_USD = 2.0

# When projected remaining runway (at current burn rate) drops below this
# many seconds, meter_job_usage flags a warning the caller should surface
# to the customer (CLI output / email) with a fresh top-up link.
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

    Allows the balance to go up to GRACE_BUFFER_USD negative before
    raising InsufficientBalance, instead of hard-killing the instant
    balance crosses exactly zero -- see the module docstring for why.
    """
    cost = (seconds_elapsed / 3600) * price_per_hour
    balance = get_balance(user_id)

    if balance - cost < -GRACE_BUFFER_USD:
        raise InsufficientBalance(
            f"job {job_id} balance depleted mid-run (${balance:.2f}, "
            f"grace buffer ${GRACE_BUFFER_USD:.2f} exhausted) -- caller "
            f"must terminate the instance"
        )

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
