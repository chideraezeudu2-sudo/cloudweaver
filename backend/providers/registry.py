"""
Central place that knows about active providers. The broker never
imports a provider module directly -- it goes through this registry.

LAUNCH SCOPE: only Vast.ai + RunPod are active. Both let you generate an
API key with zero deposit, unlike Lambda Labs/DigitalOcean (require a
funded payment method) and Crusoe (enterprise-ish onboarding, and its
adapter isn't finished -- see providers/crusoe.py). Their adapter files
are left in the repo for a fast-follow once there's revenue to fund those
accounts -- re-enabling one is a one-line change here, nothing else.
"""

from __future__ import annotations

from .base import ProviderAdapter
from .runpod import RunPodAdapter
from .vast import VastAdapter

# Order here is just registration order, NOT priority -- the broker always
# re-sorts candidates by live price_per_hour before trying any of them.
_ADAPTER_CLASSES = {
    "vast": VastAdapter,
    "runpod": RunPodAdapter,
    # "lambda_labs": LambdaLabsAdapter,   # deferred -- needs funded account
    # "crusoe": CrusoeAdapter,            # deferred -- adapter unfinished
    # "digitalocean": DigitalOceanAdapter,  # deferred -- needs funded account
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
