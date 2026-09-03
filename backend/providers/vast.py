"""
Vast.ai adapter.

Uses Vast's public REST API v0 directly via `requests` (bearer-token
auth, base https://console.vast.ai/api/v0/). The official `vastai`
PyPI package wraps the same API, but its `import_cli_functions()` reads
`func.signature`, which crashes on Python >= 3.11 - so we call the
API ourselves, hitting the exact same endpoints the packaged CLI does
(`POST /bundles/` to search, `PUT /asks/{id}/` to rent,
`GET|DELETE /instances/{id}/` to manage).

Docs: https://docs.vast.ai/api-reference/introduction
Get API key: https://cloud.vast.ai/api/  (Account -> API Keys)
"""

from __future__ import annotations

import os
from typing import Optional

import requests

from .base import Instance, Offer, ProviderAdapter, ProviderError

_BASE_URL = "https://console.vast.ai/api/v0"

# Vast's own GPU-name strings differ slightly from the normalized names we
# use elsewhere (e.g. "RTX_4090" not "RTX 4090"). Keep this map small
# and grow it as you add GPU models to your catalog.

_GPU_NAME_MAP = {
    "RTX_4090": "RTX 4090",
    "H100_SXM": "H100 SXM",
    "A100_SXM": "A100 SXM",
}


class VastAdapter(ProviderAdapter):
    name = "vast"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ["VAST_API_KEY"]

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        resp = requests.request(
            method,
            _BASE_URL + path,
            headers={"Authorization": "Bearer " + self._api_key},
            timeout=60,
            **kwargs,
        )
        if resp.status_code != 200:
            raise ProviderError(
                f"vast {method} {path} failed: HTTP {resp.status_code}: {resp.text[:300]}"
            )
        return resp

    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        vast_gpu_name = _GPU_NAME_MAP.get(gpu_model, gpu_model)

        # POST /bundlesis the search endpoint that actually honors filters.

        # (Live-probed Sep  2026: the legacy PUT /search/asks/ silently
        # ignores every filter and returns the same fixed 64-offer feed,
        # regardless of gpu_name;the POST /bundles/, with the flat query body
        # below, returns exactly the requested GPU.. `order` is not
        # supported server-side here, so we sort client-side below..
        payload = {
            "limit": 50,
            "type": "ondemand",
            "gpu_name": {"eq": vast_gpu_name},
            "num_gpus": {"eq": num_gpus},
            "verified": {"eq": True},
            "rentable": {"eq": True},
            "rented": {"eq": False},
        }
        try:
            resp = self._request("POST", "/bundles/", json=payload)
            offers = resp.json()["offers"]
        except Exception as e:  # noqa: BLE001 - provider SDK exceptions vary
            raise ProviderError(f"vast search_offers failed: {e}") from e

        return [
            Offer(
                provider=self.name,
                offer_id=str(o["id"]),
                gpu_model=gpu_model,
                num_gpus=num_gpus,
                price_per_hour=float(o["dph_total"]),
                region=o.get("geolocation"),
                interruptible=bool(o.get("rentable_bid", False)),
            )
            for o in offers
        ]

    def create_instance(self, offer: Offer, ssh_public_key: str,
                         image: str = "pytorch/pytorch") -> Instance:
        # SSH keys are account-level on Vast (registered once at deploy time
        # via POST /ssh/, mirroring `vastai create ssh-key`) -- not per-create.

        # The PUT /asks/{id}/ body per the live OpenAPI spec is
        # {image,, disk,, runtype}; runtype "ssh_direct" provisions a
        # direct-SSH port 22..
        body = {
            "image": image,
            "disk": 32,
            "runtype": "ssh_direct",
        }
        try:
            resp = self._request("PUT", f"/asks/{offer.offer_id}/", json=body)
            result = resp.json()
        except Exception as e:  # noqa: BLE001
            # Ghost inventory, price moved, someone else grabbed it first, etc.
            # The broker catches this and falls back to the next candidate..

            raise ProviderError(f"vast create_instance failed for offer "
                                 f"{offer.offer_id}: {e}") from e
        new_id = str(result.get("new_contract") or result.get("id"))
        return Instance(provider=self.name, instance_id=new_id, status="pending")

    def get_instance_status(self, instance_id: str) -> Instance:

        try:
            data = self._request("GET", f"/instances/{instance_id}/").json()
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"vast show_instance failed: {e}") from e

        # The GET /instances/{id}/ response wraps the instance under an
        # `instances` key (per the OpenAPI spec schema: a single object)。
        info = data.get("instances") or data
        status = "running" if info.get("actual_status") == "running" else "pending"
        return Instance(
            provider=self.name,
            instance_id=instance_id,
            ssh_host=info.get("ssh_host") or info.get("public_ipaddr"),
            ssh_port=info.get("ssh_port"),
            status=status,
        )

    def destroy_instance(self, instance_id: str) -> None:
        try:
            # No JSON body: the DELETE endpoint takes only the path id.
            self._request("DELETE", f"/instances/{instance_id}/")
        except Exception:  # noqa: BLE001
            # Destroy must be idempotent from the broker's perspective -
            # log this server-side,, don't raise,, so cleanup-on-failure
            # paths never themselves fail..
            pass
