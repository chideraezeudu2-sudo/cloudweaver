"""
Vast.ai adapter.

Uses the official `vastai` PyPI package (`pip install vastai`), which wraps
Vast's REST API (bearer-token auth, base https://console.vast.ai/api/v0/).
This is the same package/pattern SkyPilot itself uses under the hood
(sky/provision/vast/utils.py) — confirmed against the vendored SkyPilot repo,
not guessed.

Docs: https://docs.vast.ai/api-reference/introduction
Get API key: https://cloud.vast.ai/api/  (Account -> API Keys)
"""

from __future__ import annotations

import os
from typing import Optional

from .base import Instance, Offer, ProviderAdapter, ProviderError

try:
    from vastai import VastAI  # pip install vastai
except ImportError:  # pragma: no cover - allows spec/tests to import module
    VastAI = None  # type: ignore


# Vast's own GPU-name strings differ slightly from the normalized names we
# use elsewhere (e.g. "RTX_4090" not "RTX 4090"). Keep this map small and
# grow it as you add GPU models to your catalog.
_GPU_NAME_MAP = {
    "RTX_4090": "RTX 4090",
    "H100_SXM": "H100 SXM",
    "A100_SXM": "A100 SXM",
}


class VastAdapter(ProviderAdapter):
    name = "vast"

    def __init__(self, api_key: Optional[str] = None):
        if VastAI is None:
            raise ImportError("pip install vastai")
        self._client = VastAI(api_key=api_key or os.environ["VAST_API_KEY"])

    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        vast_gpu_name = _GPU_NAME_MAP.get(gpu_model, gpu_model)
        query = f'gpu_name="{vast_gpu_name}" num_gpus={num_gpus} rentable=true'
        try:
            offers = self._client.search_offers(query=query, order="dph_total")
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
        try:
            result = self._client.create_instance(
                id=int(offer.offer_id),
                image=image,
                ssh=True,
                direct=True,
                disk=32,
            )
        except Exception as e:  # noqa: BLE001
            # THIS is the live-probe failing — ghost inventory, price moved,
            # someone else grabbed it first, etc. The broker catches this.
            raise ProviderError(f"vast create_instance failed for offer "
                                 f"{offer.offer_id}: {e}") from e

        new_id = str(result.get("new_contract") or result.get("id"))
        return Instance(provider=self.name, instance_id=new_id, status="pending")

    def get_instance_status(self, instance_id: str) -> Instance:
        try:
            info = self._client.show_instance(id=int(instance_id))
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"vast show_instance failed: {e}") from e

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
            self._client.destroy_instance(id=int(instance_id))
        except Exception:  # noqa: BLE001
            # Destroy must be idempotent from the broker's perspective —
            # log this server-side, don't raise, so cleanup-on-failure
            # paths never themselves fail.
            pass
