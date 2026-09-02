"""
Crusoe Cloud adapter.

Crusoe's API is REST under https://api.crusoecloud.com/v1alpha5/, scoped by
project_id. Crusoe does not publish a simple public price-per-hour listing
endpoint the way Vast/RunPod do -- pricing has historically required a
quote/contract step. TREAT THIS ADAPTER AS THE LEAST FINISHED OF THE FIVE:
OpenHands should confirm current pricing-lookup endpoints against
https://docs.crusoecloud.com/api/ before wiring this into the live price
feed, and may need to fall back to a static/contracted rate per GPU type
looked up from your own Crusoe account settings instead of a live quote.

Docs: https://docs.crusoecloud.com/api/
Get API key: Crusoe console -> Access Keys (used for HMAC-SHA256 request
signing, NOT a simple bearer token -- different auth shape than the other
four providers, budget extra implementation time for this one specifically).
"""

from __future__ import annotations

import os
from typing import Optional

import requests

from .base import Instance, Offer, ProviderAdapter, ProviderError

_BASE_URL = "https://api.crusoecloud.com/v1alpha5"

_TYPE_MAP = {
    "H100_SXM": "h100-80gb-sxm.1x",
    "A100_SXM": "a100-80gb-sxm.1x",
    # RTX 4090 not confirmed available on Crusoe as of this writing --
    # OpenHands: verify via `crusoe compute vms types` before enabling.
}


class CrusoeAdapter(ProviderAdapter):
    name = "crusoe"

    def __init__(self, access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 project_id: Optional[str] = None):
        # NOTE: Crusoe uses HMAC-SHA256 signed requests, not a plain bearer
        # token. This constructor stores raw keys; OpenHands must implement
        # the actual signing logic (see Crusoe's auth docs) in _request()
        # below before this adapter will work against the real API.
        self._access_key = access_key or os.environ["CRUSOE_ACCESS_KEY"]
        self._secret_key = secret_key or os.environ["CRUSOE_SECRET_KEY"]
        self._project_id = project_id or os.environ["CRUSOE_PROJECT_ID"]

    def _request(self, method: str, path: str, **kwargs) -> dict:
        # TODO(OpenHands): implement HMAC-SHA256 request signing per
        # https://docs.crusoecloud.com/api/ before this adapter is usable.
        # Raising here deliberately so a missing implementation fails loudly
        # instead of silently sending unsigned (rejected) requests.
        raise NotImplementedError(
            "Crusoe HMAC request signing not yet implemented — see "
            "docstring at top of providers/crusoe.py"
        )

    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        vm_type = _TYPE_MAP.get(gpu_model)
        if vm_type is None:
            return []
        data = self._request(
            "GET", f"projects/{self._project_id}/compute/vms/types")
        # Response shape per Crusoe docs: {"items": [{"product_name": ...}]}
        offers = []
        for item in data.get("items", []):
            if item.get("product_name") != vm_type:
                continue
            offers.append(Offer(
                provider=self.name,
                offer_id=vm_type,
                gpu_model=gpu_model,
                num_gpus=num_gpus,
                # Crusoe's type-listing endpoint does not return live price
                # in all API versions -- OpenHands should confirm and wire
                # the correct pricing field/endpoint here.
                price_per_hour=float(item.get("price_per_hour", 0.0)),
                interruptible=False,
            ))
        return offers

    def create_instance(self, offer: Offer, ssh_public_key: str,
                         image: str = "ubuntu22.04:latest") -> Instance:
        payload = {
            "name": f"broker-{offer.offer_id}",
            "type": offer.offer_id,
            "location": offer.region or "us-southcentral1-a",
            "image": image,
            "ssh_public_key": ssh_public_key,
        }
        data = self._request(
            "POST", f"projects/{self._project_id}/compute/vms/instances",
            json=payload)
        instance_id = data.get("id") or data.get("vm_id")
        if not instance_id:
            raise ProviderError("crusoe create_instance returned no id")
        return Instance(provider=self.name, instance_id=instance_id, status="pending")

    def get_instance_status(self, instance_id: str) -> Instance:
        data = self._request(
            "GET",
            f"projects/{self._project_id}/compute/vms/instances/{instance_id}")
        status = "running" if data.get("state") == "running" else "pending"
        return Instance(
            provider=self.name,
            instance_id=instance_id,
            ssh_host=data.get("network_interfaces", [{}])[0].get("public_ipv4"),
            ssh_port=22,
            status=status,
        )

    def destroy_instance(self, instance_id: str) -> None:
        try:
            self._request(
                "DELETE",
                f"projects/{self._project_id}/compute/vms/instances/{instance_id}")
        except Exception:  # noqa: BLE001
            pass
