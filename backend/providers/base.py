"""
Common interface every provider adapter must implement.

Modeled on the same shape SkyPilot uses internally (search offers -> create
instance -> poll status -> destroy instance), but simplified for a
single-tenant broker that reserves on ITS OWN provider accounts, not the
end user's.

Every adapter function should raise ProviderError on failure so the broker
can catch it uniformly and move to the next fallback candidate.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional


class ProviderError(Exception):
    """Raised whenever a provider call fails — ghost inventory, API error,
    auth failure, etc. The broker treats ALL of these the same way: log it,
    mark the offer bad, try the next candidate."""


@dataclass
class Offer:
    """A single rentable GPU offer, normalized across providers."""
    provider: str          # "vast", "runpod", "lambda_labs", "crusoe", "digitalocean"
    offer_id: str          # provider-specific id needed to actually rent this
    gpu_model: str          # normalized, e.g. "RTX_4090", "H100_SXM"
    num_gpus: int
    price_per_hour: float   # OUR COST, not the customer price
    region: Optional[str] = None
    interruptible: bool = False  # True for spot/community-tier capacity


@dataclass
class Instance:
    """A provisioned, running instance."""
    provider: str
    instance_id: str        # id needed to destroy/poll this instance
    ssh_host: Optional[str] = None
    ssh_port: Optional[int] = None
    ssh_user: str = "root"
    status: str = "pending"  # pending | running | failed | terminated


class ProviderAdapter(abc.ABC):
    """One of these per provider. Keep every adapter to just these four
    methods — the broker's fallback/verification logic lives OUTSIDE the
    adapters, not inside them, so every provider behaves identically from
    the broker's point of view."""

    name: str

    @abc.abstractmethod
    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        """Return live offers for a GPU model, cheapest first. This is a
        REAL API call each time — never serve this from a stale cache
        directly to the broker's reserve step (see core/broker.py)."""

    @abc.abstractmethod
    def create_instance(self, offer: Offer, ssh_public_key: str,
                         image: str = "pytorch/pytorch") -> Instance:
        """Attempt to actually reserve the offer. This IS the live-probe —
        if the offer is ghost inventory, this call fails and raises
        ProviderError. There is no separate 'check availability' step;
        attempting the real reservation is the check."""

    @abc.abstractmethod
    def get_instance_status(self, instance_id: str) -> Instance:
        """Poll until status == 'running' and ssh_host is populated."""

    @abc.abstractmethod
    def destroy_instance(self, instance_id: str) -> None:
        """Tear down. Must be safe to call twice (idempotent) — the broker
        calls this aggressively on any failure path, including benchmark
        failures, so a provider that errors on double-destroy will raise
        false alarms."""
