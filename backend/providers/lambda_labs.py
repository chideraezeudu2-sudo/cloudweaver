"""
Lambda Labs adapter.

Lambda's Cloud API uses HTTP Basic auth with the API key as the username and
an empty password (confirmed in Lambda's own docs: `curl -u $API_KEY:`).
No spot/interruptible tier — Lambda is on-demand only, which makes it a good
FALLBACK provider in the broker's chain rather than a primary cost source
(see core/broker.py) since it won't be cheapest, but it's the most reliable.

Docs: https://docs.lambda.ai (Cloud API)
Get API key: Lambda Cloud console -> API keys
Note: an SSH key must already exist in your Lambda account (ssh_key_names)
before you can launch — this is account setup, not something the API can
do on your behalf. See BUILD_SPEC.md, Lambda Labs section.
"""

from __future__ import annotations

import os
from typing import Optional

import requests

from .base import Instance, Offer, ProviderAdapter, ProviderError

_BASE_URL = "https://cloud.lambda.ai/api/v1"

_INSTANCE_TYPE_MAP = {
    "RTX_4090": None,  # Lambda does not currently offer 4090s — omit from
                        # the broker's candidate list for this GPU model.
    "H100_SXM": "gpu_1x_h100_sxm5",
    "A100_SXM": "gpu_1x_a100_sxm4",
}


class LambdaLabsAdapter(ProviderAdapter):
    name = "lambda_labs"

    def __init__(self, api_key: Optional[str] = None,
                 ssh_key_name: Optional[str] = None):
        self._api_key = api_key or os.environ["LAMBDA_API_KEY"]
        # Must match an SSH key name already registered in the Lambda console.
        self._ssh_key_name = ssh_key_name or os.environ["LAMBDA_SSH_KEY_NAME"]

    def _request(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(
            method, f"{_BASE_URL}/{path}",
            auth=(self._api_key, ""), timeout=20, **kwargs,
        )
        if resp.status_code >= 400:
            raise ProviderError(f"lambda_labs {path} failed "
                                 f"({resp.status_code}): {resp.text}")
        return resp.json()

    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        instance_type = _INSTANCE_TYPE_MAP.get(gpu_model)
        if instance_type is None:
            return []  # this GPU model isn't offered here at all

        try:
            data = self._request("GET", "instance-types")
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"lambda_labs search failed: {e}") from e

        offers = []
        entry = data.get("data", {}).get(instance_type)
        if not entry:
            return []
        for region in entry.get("regions_with_capacity_available", []):
            offers.append(Offer(
                provider=self.name,
                offer_id=instance_type,
                gpu_model=gpu_model,
                num_gpus=num_gpus,
                price_per_hour=entry["instance_type"]["price_cents_per_hour"] / 100,
                region=region["name"],
                interruptible=False,
            ))
        return offers

    def create_instance(self, offer: Offer, ssh_public_key: str,
                         image: str = "") -> Instance:
        payload = {
            "region_name": offer.region,
            "instance_type_name": offer.offer_id,
            "ssh_key_names": [self._ssh_key_name],
            "quantity": 1,
        }
        try:
            data = self._request("POST", "instance-operations/launch", json=payload)
        except Exception as e:  # noqa: BLE001
            # Most common failure here IS the ghost-inventory case: capacity
            # showed available in instance-types but launch fails anyway.
            raise ProviderError(f"lambda_labs launch failed: {e}") from e

        ids = data.get("data", {}).get("instance_ids", [])
        if not ids:
            raise ProviderError("lambda_labs launch returned no instance id")
        return Instance(provider=self.name, instance_id=ids[0], status="pending")

    def get_instance_status(self, instance_id: str) -> Instance:
        try:
            data = self._request("GET", f"instances/{instance_id}")
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"lambda_labs status check failed: {e}") from e

        info = data.get("data", {})
        status = "running" if info.get("status") == "active" else "pending"
        return Instance(
            provider=self.name,
            instance_id=instance_id,
            ssh_host=info.get("ip"),
            ssh_port=22,
            status=status,
        )

    def destroy_instance(self, instance_id: str) -> None:
        try:
            self._request("POST", "instance-operations/terminate",
                           json={"instance_ids": [instance_id]})
        except Exception:  # noqa: BLE001
            pass
