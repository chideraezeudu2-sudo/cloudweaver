"""
DigitalOcean GPU Droplets adapter.

Simplest auth of the five: a personal access token as a bearer header
against the standard v2 Droplets API. DigitalOcean does not have a
marketplace/spot tier -- treat this like Lambda Labs, a reliable but
never-cheapest fallback rather than a primary cost source.

Docs: https://docs.digitalocean.com/reference/api/digitalocean/
Get API key: DigitalOcean control panel -> API -> Generate New Token
(needs read+write scope)
"""

from __future__ import annotations

import os
import time
from typing import Optional

import requests

from .base import Instance, Offer, ProviderAdapter, ProviderError

_BASE_URL = "https://api.digitalocean.com/v2"

# DigitalOcean GPU Droplet size slugs -- confirm current slugs via
# GET /v2/sizes before relying on these; DO adds/renames GPU plans
# periodically.
_SIZE_SLUG_MAP = {
    "H100_SXM": "gpu-h100x1-80gb",
    "A100_SXM": "gpu-a100x1-80gb",
}

_STATIC_PRICE_PER_HOUR = {
    # DigitalOcean's pricing API returns hourly rates per size; this is a
    # placeholder OpenHands should replace with a live GET /v2/sizes call
    # rather than hardcoding, since GPU pricing changes.
    "gpu-h100x1-80gb": 3.39,
    "gpu-a100x1-80gb": 1.99,
}


class DigitalOceanAdapter(ProviderAdapter):
    name = "digitalocean"

    def __init__(self, api_token: Optional[str] = None,
                 ssh_key_id: Optional[str] = None):
        self._token = api_token or os.environ["DO_API_TOKEN"]
        # Must be an SSH key ID already uploaded to the DO account.
        self._ssh_key_id = ssh_key_id or os.environ["DO_SSH_KEY_ID"]

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        slug = _SIZE_SLUG_MAP.get(gpu_model)
        if slug is None:
            return []
        try:
            resp = requests.get(f"{_BASE_URL}/sizes",
                                 headers=self._headers(), timeout=20)
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"digitalocean sizes lookup failed: {e}") from e

        sizes = {s["slug"]: s for s in resp.json().get("sizes", [])}
        matched = sizes.get(slug)
        if not matched or not matched.get("available", False):
            return []  # ghost inventory caught here already, before we
                       # even attempt a create

        return [Offer(
            provider=self.name,
            offer_id=slug,
            gpu_model=gpu_model,
            num_gpus=num_gpus,
            price_per_hour=matched.get("price_hourly",
                                        _STATIC_PRICE_PER_HOUR.get(slug, 0.0)),
            interruptible=False,
        )]

    def create_instance(self, offer: Offer, ssh_public_key: str,
                         image: str = "gpu-h100x1-base") -> Instance:
        payload = {
            "name": f"broker-{int(time.time())}",
            "region": offer.region or "nyc2",
            "size": offer.offer_id,
            "image": image,
            "ssh_keys": [self._ssh_key_id],
        }
        try:
            resp = requests.post(f"{_BASE_URL}/droplets",
                                  headers=self._headers(), json=payload, timeout=20)
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"digitalocean create failed for "
                                 f"{offer.offer_id}: {e}") from e

        droplet = resp.json()["droplet"]
        return Instance(provider=self.name, instance_id=str(droplet["id"]),
                         status="pending")

    def get_instance_status(self, instance_id: str) -> Instance:
        try:
            resp = requests.get(f"{_BASE_URL}/droplets/{instance_id}",
                                 headers=self._headers(), timeout=20)
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"digitalocean status check failed: {e}") from e

        droplet = resp.json()["droplet"]
        ip = next(
            (n["ip_address"] for n in droplet["networks"]["v4"]
             if n["type"] == "public"), None)
        status = "running" if droplet["status"] == "active" and ip else "pending"
        return Instance(provider=self.name, instance_id=instance_id,
                         ssh_host=ip, ssh_port=22, status=status)

    def destroy_instance(self, instance_id: str) -> None:
        try:
            requests.delete(f"{_BASE_URL}/droplets/{instance_id}",
                             headers=self._headers(), timeout=20)
        except Exception:  # noqa: BLE001
            pass
