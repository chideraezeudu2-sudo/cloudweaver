"""
This is the piece we spent the whole conversation designing: don't trust
the scraped price cache, live-probe by actually attempting to reserve,
benchmark on boot before ever billing the customer, and fall back
automatically through candidates instead of surfacing a failure.

The scraped price cache (updated every few minutes by a separate
background job -- see core/price_cache.py, not included here since it's
a straightforward cron-style scraper like gputable.dev's) is used ONLY to
decide which 3-5 candidates to try first, cheapest-looking to most
expensive. It is NEVER used as the actual quoted price.
"""

from __future__ import annotations

import logging
import os
import tempfile
import time
from dataclasses import dataclass

from providers.base import Instance, Offer, ProviderError
from providers.registry import get_all_adapters

from .benchmark import run_benchmark

logger = logging.getLogger("broker")

MARGIN_MULTIPLIER = 1.30   # customer pays cost * this, minimum
MIN_MARGIN_PER_HOUR = 0.03  # ...or at least this much per hour, whichever's higher
MAX_CANDIDATES_TO_TRY = 5   # how many offers to attempt before giving up
PROVISION_TIMEOUT_SECONDS = 120


class NoCapacityAvailable(Exception):
    """Every candidate failed -- ghost inventory, benchmark failure, or
    provider error, across the board. Surface this to the customer as
    'no capacity right now', not a generic 500."""


@dataclass
class ReservationResult:
    instance: Instance
    offer: Offer
    customer_price_per_hour: float
    benchmark_power_watts: float
    benchmark_tflops: float


def quote_and_reserve(gpu_model: str, num_gpus: int, ssh_public_key: str,
                       ssh_private_key_path: str,
                       image: str = "pytorch/pytorch") -> ReservationResult:
    """
    The whole verification pipeline in one function:
      1. Pull ranked candidates from the price cache (cheap hint, not truth)
      2. For each candidate, in order:
         a. Attempt the REAL reservation (this is the live-probe)
         b. If it succeeds, wait for it to boot
         c. Run the boot-time benchmark
         d. If the benchmark fails, destroy it and try the next candidate
      3. First candidate that survives all three checks is what the
         customer gets billed for -- at THIS point, not before.
    """
    adapters = get_all_adapters()
    if not adapters:
        raise NoCapacityAvailable("no provider adapters configured")

    candidates: list[Offer] = []
    for adapter in adapters.values():
        try:
            candidates.extend(adapter.search_offers(gpu_model, num_gpus))
        except ProviderError as e:
            logger.warning("search_offers failed for %s: %s", adapter.name, e)

    if not candidates:
        raise NoCapacityAvailable(f"no offers found anywhere for {gpu_model}")

    candidates.sort(key=lambda o: o.price_per_hour)
    candidates = candidates[:MAX_CANDIDATES_TO_TRY]

    for offer in candidates:
        adapter = adapters[offer.provider]
        instance = None
        try:
            # --- Live probe: the attempt itself IS the availability check ---
            instance = adapter.create_instance(offer, ssh_public_key, image)
            logger.info("reserved %s on %s at $%.3f/hr, waiting for boot",
                        instance.instance_id, offer.provider, offer.price_per_hour)

            instance = _wait_for_running(adapter, instance.instance_id)

            # --- Boot-time benchmark ---
            result = run_benchmark(
                ssh_host=instance.ssh_host,
                ssh_port=instance.ssh_port,
                ssh_user=instance.ssh_user,
                ssh_private_key_path=ssh_private_key_path,
                gpu_model=gpu_model,
            )
            if not result.passed:
                logger.warning("benchmark failed on %s/%s: %s -- falling back",
                                offer.provider, instance.instance_id, result.reason)
                adapter.destroy_instance(instance.instance_id)
                continue

            customer_price = max(
                offer.price_per_hour * MARGIN_MULTIPLIER,
                offer.price_per_hour + MIN_MARGIN_PER_HOUR,
            )
            return ReservationResult(
                instance=instance,
                offer=offer,
                customer_price_per_hour=round(customer_price, 4),
                benchmark_power_watts=result.measured_power_watts or 0.0,
                benchmark_tflops=result.measured_tflops or 0.0,
            )

        except ProviderError as e:
            logger.warning("candidate %s/%s failed: %s -- falling back",
                            offer.provider, offer.offer_id, e)
            if instance is not None:
                adapter.destroy_instance(instance.instance_id)
            continue
        except TimeoutError:
            logger.warning("candidate %s/%s never booted -- falling back",
                            offer.provider, offer.offer_id)
            if instance is not None:
                adapter.destroy_instance(instance.instance_id)
            continue

    raise NoCapacityAvailable(
        f"all {len(candidates)} candidates failed for {gpu_model} "
        f"(ghost inventory, benchmark rejection, or provider error)"
    )


def _wait_for_running(adapter, instance_id: str,
                       timeout_seconds: int = PROVISION_TIMEOUT_SECONDS,
                       poll_interval: int = 5) -> Instance:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        instance = adapter.get_instance_status(instance_id)
        if instance.status == "running" and instance.ssh_host:
            return instance
        if instance.status == "failed":
            raise ProviderError(f"instance {instance_id} entered failed state")
        time.sleep(poll_interval)
    raise TimeoutError(f"instance {instance_id} did not boot in "
                        f"{timeout_seconds}s")
