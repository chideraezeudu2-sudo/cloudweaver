"""
RunPod adapter.

RunPod's GraphQL API takes the key as a query param on the endpoint URL
(https://api.runpod.io/graphql?api_key=...), confirmed against RunPod's own
docs (docs.runpod.io/sdks/graphql/manage-pods). A newer REST API v2 exists
in beta as of mid-2026 (bearer-token auth) — worth re-checking whether it's
GA before OpenHands finalizes this adapter; swap this for the REST version
if so, the Offer/Instance shape returned to the broker doesn't change.

Docs: https://docs.runpod.io/sdks/graphql/manage-pods
Get API key: RunPod console -> Settings -> API Keys
"""

from __future__ import annotations

import os
from typing import Optional

import requests

from .base import Instance, Offer, ProviderAdapter, ProviderError

_GRAPHQL_URL = "https://api.runpod.io/graphql"

# RunPod's gpuTypeId strings (confirmed via their docs example:
# "NVIDIA RTX A6000"). Extend as you add GPU models.
_GPU_TYPE_ID_MAP = {
    "RTX_4090": "NVIDIA GeForce RTX 4090",
    "H100_SXM": "NVIDIA H100 80GB HBM3",
    "A100_SXM": "NVIDIA A100-SXM4-80GB",
}


class RunPodAdapter(ProviderAdapter):
    name = "runpod"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.environ["RUNPOD_API_KEY"]

    def _query(self, query: str, timeout: int = 20) -> dict:
        resp = requests.post(
            _GRAPHQL_URL,
            params={"api_key": self._api_key},
            json={"query": query},
            timeout=timeout,
        )
        data = resp.json()
        if "errors" in data:
            raise ProviderError(f"runpod graphql error: {data['errors']}")
        return data["data"]

    def search_offers(self, gpu_model: str, num_gpus: int = 1) -> list[Offer]:
        gpu_type_id = _GPU_TYPE_ID_MAP.get(gpu_model, gpu_model)
        q = f'''
        query {{
          gpuTypes(input: {{id: "{gpu_type_id}"}}) {{
            id
            communityPrice
            secureSpotPrice
          }}
        }}'''
        try:
            data = self._query(q)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"runpod search failed: {e}") from e

        offers = []
        for gt in data.get("gpuTypes", []):
            price = gt.get("communityPrice") or gt.get("secureSpotPrice")
            if price is None:
                continue
            offers.append(Offer(
                provider=self.name,
                offer_id=gt["id"],
                gpu_model=gpu_model,
                num_gpus=num_gpus,
                price_per_hour=float(price) * num_gpus,
                interruptible=True,
            ))
        return sorted(offers, key=lambda o: o.price_per_hour)

    def create_instance(self, offer: Offer, ssh_public_key: str,
                         image: str = "runpod/pytorch") -> Instance:
        mutation = f'''
        mutation {{
          podFindAndDeployOnDemand(input: {{
            cloudType: ALL
            gpuCount: {offer.num_gpus}
            gpuTypeId: "{offer.offer_id}"
            imageName: "{image}"
            containerDiskInGb: 40
            volumeInGb: 40
            name: "broker-job"
          }}) {{
            id
            machineId
          }}
        }}'''
        try:
            data = self._query(mutation)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(
                f"runpod create_instance failed for {offer.offer_id}: {e}"
            ) from e

        pod = data.get("podFindAndDeployOnDemand")
        if not pod:
            # No capacity actually available -- ghost inventory case.
            raise ProviderError(f"runpod returned no pod for {offer.offer_id}")
        return Instance(provider=self.name, instance_id=pod["id"], status="pending")

    def get_instance_status(self, instance_id: str) -> Instance:
        q = f'''
        query {{
          pod(input: {{podId: "{instance_id}"}}) {{
            desiredStatus
            runtime {{ ports {{ ip isIpPublic publicPort privatePort type }} }}
          }}
        }}'''
        try:
            data = self._query(q)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"runpod status check failed: {e}") from e

        pod = data.get("pod") or {}
        running = pod.get("desiredStatus") == "RUNNING"
        ports = (pod.get("runtime") or {}).get("ports") or []
        ssh_port_info = next((p for p in ports if p.get("privatePort") == 22), None)

        return Instance(
            provider=self.name,
            instance_id=instance_id,
            ssh_host=ssh_port_info["ip"] if ssh_port_info else None,
            ssh_port=ssh_port_info["publicPort"] if ssh_port_info else None,
            status="running" if running and ssh_port_info else "pending",
        )

    def destroy_instance(self, instance_id: str) -> None:
        mutation = f'mutation {{ podTerminate(input: {{podId: "{instance_id}"}}) }}'
        try:
            self._query(mutation)
        except Exception:  # noqa: BLE001
            pass
