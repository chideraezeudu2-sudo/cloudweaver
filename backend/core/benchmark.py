"""
Boot-time benchmark. This is the fix for the "power-capped card looks
identical on paper" problem: read the real power limit off the card, and if
that looks fine, run one tiny compute test to catch anything the power
limit alone doesn't reveal.

Runs over SSH against a freshly-provisioned instance, BEFORE the broker
hands it to the customer's job and BEFORE anything gets billed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import paramiko  # pip install paramiko

# Manufacturer-rated power limits, watts. If a card's *current* power limit
# (as reported by nvidia-smi) is below this fraction, treat it as throttled
# and reject it rather than benchmark further -- this alone catches most
# real-world cases and costs one SSH round trip.
_RATED_POWER_WATTS = {
    "RTX 4090": 450,
    "H100 SXM": 700,
    "A100 SXM": 400,
}
_MIN_POWER_FRACTION = 0.85  # below this fraction of rated power -> reject

# Expected order-of-magnitude single-precision TFLOPS for a quick matmul
# sanity check. This is NOT meant to be a precise benchmark -- it's a
# cheap smoke test to catch a card that's obviously not delivering what
# it should, in under 30 seconds.
_MIN_EXPECTED_TFLOPS = {
    "RTX 4090": 40.0,
    "H100 SXM": 200.0,
    "A100 SXM": 100.0,
}

_MATMUL_BENCH_SCRIPT = r"""
python3 - <<'PYEOF'
import torch, time
n = 8192
a = torch.randn(n, n, device='cuda', dtype=torch.float16)
b = torch.randn(n, n, device='cuda', dtype=torch.float16)
torch.cuda.synchronize()
start = time.time()
for _ in range(10):
    c = a @ b
torch.cuda.synchronize()
elapsed = time.time() - start
flops = 2 * n**3 * 10
print(f"TFLOPS:{flops / elapsed / 1e12:.2f}")
PYEOF
"""


@dataclass
class BenchmarkResult:
    passed: bool
    reason: str
    measured_power_watts: float | None = None
    measured_tflops: float | None = None


def run_benchmark(ssh_host: str, ssh_port: int, ssh_user: str,
                   ssh_private_key_path: str, gpu_model: str,
                   timeout_seconds: int = 60) -> BenchmarkResult:
    """SSH in, check the real power limit, run a quick matmul if that
    passes. Any failure here should result in the broker destroying this
    instance and falling back to the next candidate -- see core/broker.py.
    """
    rated_watts = _RATED_POWER_WATTS.get(gpu_model)
    min_tflops = _MIN_EXPECTED_TFLOPS.get(gpu_model)

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ssh_host, port=ssh_port, username=ssh_user,
                        key_filename=ssh_private_key_path,
                        timeout=timeout_seconds)
    except Exception as e:  # noqa: BLE001
        return BenchmarkResult(passed=False, reason=f"ssh connect failed: {e}")

    try:
        # Step 1: read the ACTUAL current power limit, not the advertised
        # spec. This alone catches most power-capped listings cheaply.
        _, stdout, _ = client.exec_command(
            "nvidia-smi --query-gpu=power.limit --format=csv,noheader,nounits",
            timeout=15)
        power_str = stdout.read().decode().strip().splitlines()[0]
        measured_watts = float(power_str)

        if rated_watts and measured_watts < rated_watts * _MIN_POWER_FRACTION:
            return BenchmarkResult(
                passed=False,
                reason=(f"power capped: {measured_watts}W measured vs "
                        f"{rated_watts}W rated ({rated_watts * _MIN_POWER_FRACTION:.0f}W minimum)"),
                measured_power_watts=measured_watts,
            )

        # Step 2: quick matmul to catch anything power-limit alone misses
        # (e.g. thermal throttling, shared/virtualized GPU slicing).
        _, stdout, stderr = client.exec_command(_MATMUL_BENCH_SCRIPT,
                                                 timeout=timeout_seconds)
        out = stdout.read().decode()
        err = stderr.read().decode()
        line = next((l for l in out.splitlines() if l.startswith("TFLOPS:")), None)
        if line is None:
            return BenchmarkResult(
                passed=False,
                reason=f"benchmark script produced no output; stderr: {err[:300]}",
                measured_power_watts=measured_watts,
            )
        measured_tflops = float(line.split(":")[1])

        if min_tflops and measured_tflops < min_tflops:
            return BenchmarkResult(
                passed=False,
                reason=(f"underperforming: {measured_tflops:.1f} TFLOPS "
                        f"measured vs {min_tflops:.1f} minimum expected"),
                measured_power_watts=measured_watts,
                measured_tflops=measured_tflops,
            )

        return BenchmarkResult(passed=True, reason="ok",
                                measured_power_watts=measured_watts,
                                measured_tflops=measured_tflops)
    except Exception as e:  # noqa: BLE001
        return BenchmarkResult(passed=False, reason=f"benchmark error: {e}")
    finally:
        client.close()
