"""Job metering loop (BUILD_SPEC §5).

Runs as a Render Cron Job every 5 minutes. For every job with
status='running' it:
  1. bills the elapsed interval since last_metered_at via
     wallet.meter_job_usage()
  2. destroys the instance + marks the job terminated if the balance
     runs out (InsufficientBalance) or max_hours is exceeded
  3. otherwise advances last_metered_at

Entrypoint for the cron: `python -m core.metering`.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from core import db, wallet
from providers.registry import get_all_adapters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metering")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def meter_once() -> dict:
    """One pass over all running jobs. Returns a summary dict."""
    adapters = get_all_adapters()
    jobs = db.list_running_jobs()
    summary = {"checked": len(jobs), "billed": 0, "terminated": 0, "errors": 0}

    for job in jobs:
        job_id = job["id"]
        user_id = job["user_id"]
        price_per_hour = float(job["price_per_hour"])
        max_hours = float(job.get("max_hours") or 0)

        # Elapsed since the last billed interval boundary.
        last = job.get("last_metered_at") or job.get("started_at")
        try:
            last_dt = datetime.fromisoformat(last.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            last_dt = datetime.now(timezone.utc)
        seconds = int((datetime.now(timezone.utc) - last_dt).total_seconds())

        # Hard stop: customer's requested max runtime exceeded.
        started = job.get("started_at")
        try:
            started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            started_dt = last_dt
        if max_hours and (datetime.now(timezone.utc) - started_dt).total_seconds() \
                > max_hours * 3600:
            _terminate(job, adapters, "completed")
            summary["terminated"] += 1
            continue

        try:
            wallet.meter_job_usage(user_id, job_id, seconds, price_per_hour)
            db.set_low_balance_warning(job_id, False)
        except wallet.LowBalanceWarning as w:
            # Debit succeeded -- this just flags the job so `gpu-deploy
            # jobs` shows a warning + the customer can top up before the
            # grace buffer runs out. Not an error.
            db.set_low_balance_warning(job_id, True)
            logger.info("job %s low balance: %s", job_id, w)
        except wallet.InsufficientBalance:
            _terminate(job, adapters, "terminated_no_balance")
            summary["terminated"] += 1
            continue
        except Exception as e:  # noqa: BLE001
            logger.exception("metering failed for job %s", job_id)
            summary["errors"] += 1
            continue

        db.get_supabase().table("jobs").update(
            {"last_metered_at": _now_iso()}).eq("id", job_id).execute()
        summary["billed"] += 1

    return summary


def _terminate(job: dict, adapters: dict, status: str) -> None:
    """Destroy the instance and mark the job terminal."""
    job_id = job["id"]
    provider = job["provider"]
    instance_id = job["provider_instance_id"]

    adapter = adapters.get(provider)
    if adapter is not None:
        try:
            adapter.destroy_instance(instance_id)
        except Exception as e:  # noqa: BLE001
            logger.warning("destroy failed for %s/%s: %s", provider, instance_id, e)
    else:
        logger.warning("no adapter for provider %s (instance %s left running)",
                       provider, instance_id)

    db.update_job_status(job_id, status, ended_at=_now_iso())
    logger.info("job %s -> %s", job_id, status)


def main() -> None:
    summary = meter_once()
    logger.info("metering pass complete: %s", summary)


if __name__ == "__main__":
    main()
