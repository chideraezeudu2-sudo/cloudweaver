"""
Central place that knows about all five providers. The broker never
imports a provider module directly -- it goes through this registry, so
adding a 6th provider later means writing one adapter file and adding one
line here, nothing else changes.
"""

from __future__ import annotations

from .base import ProviderAdapter
from .crusoe import CrusoeAdapter
from .digitalocean import DigitalOceanAdapter
from .lambda_labs import LambdaLabsAdapter
from .runpod import RunPodAdapter
from .vast import VastAdapter

# Order here is just registration order, NOT priority -- the broker always
# re-sorts candidates by live price_per_hour before trying any of them.
_ADAPTER_CLASSES = {
    "vast": VastAdapter,
    "runpod": RunPodAdapter,
    "lambda_labs": LambdaLabsAdapter,
    "crusoe": CrusoeAdapter,
    "digitalocean": DigitalOceanAdapter,
}


def get_all_adapters() -> dict[str, ProviderAdapter]:
    """Instantiate every provider adapter. Any single provider failing to
    construct (e.g. missing env var / API key) should not take down the
    whole broker -- it's just excluded from that request's candidate list.
    """
    adapters = {}
    for name, cls in _ADAPTER_CLASSES.items():
        try:
            adapters[name] = cls()
        except Exception:  # noqa: BLE001
            # Missing credentials for this provider -- log server-side in
            # the real implementation, skip it here.
            continue
    return adapters
