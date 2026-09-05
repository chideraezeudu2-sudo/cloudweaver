"""
cloudweaver CLI. This is the ENTIRE v1 product surface, on purpose --
no website, no dashboard. Every command just calls the backend API.

Install: pip install -e .   (see cli/pyproject.toml)
Config: stores the API key + backend URL in ~/.cloudweaver/config.json
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import click
import requests

CONFIG_DIR = Path.home() / ".cloudweaver"
CONFIG_PATH = CONFIG_DIR / "config.json"


def _load_config() -> dict:
    if not CONFIG_PATH.exists():
        click.echo("Not logged in. Run `cloudweaver login` first.", err=True)
        sys.exit(1)
    return json.loads(CONFIG_PATH.read_text())


def _api(method: str, path: str, **kwargs) -> requests.Response:
    cfg = _load_config()
    headers = {"Authorization": f"Bearer {cfg['api_key']}"}
    headers.update(kwargs.pop("headers", {}))
    resp = requests.request(method, f"{cfg['backend_url']}{path}",
                             headers=headers, timeout=120, **kwargs)
    if resp.status_code >= 400:
        click.echo(f"Error {resp.status_code}: {resp.text}", err=True)
        sys.exit(1)
    return resp


@click.group()
def cli():
    """cloudweaver — rent the cheapest verified-available GPU, from your terminal."""


@cli.command()
@click.option("--api-key", prompt=True, hide_input=True)
@click.option("--backend-url", default="https://api.yourbroker.dev")
def login(api_key: str, backend_url: str):
    """Save your API key locally."""
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({
        "api_key": api_key, "backend_url": backend_url,
    }))
    click.echo("Logged in.")


@cli.command("add-funds")
@click.argument("tier", type=click.Choice(["5", "10", "20", "50", "100"]))
def add_funds(tier: str):
    """Get a Paddle checkout link to add credits to your wallet.

    Paddle requires picking from a fixed set of amounts rather than
    typing any dollar figure -- $5 / $10 / $20 / $50 / $100.

    Example: cloudweaver add-funds 20
    """
    resp = _api("POST", "/wallet/add-funds", json={"tier_usd": int(tier)})
    url = resp.json()["checkout_url"]
    click.echo(f"Complete payment here: {url}")


@cli.command()
def balance():
    """Show your current wallet balance."""
    resp = _api("GET", "/wallet/balance")
    click.echo(f"${resp.json()['balance_usd']:.2f}")


@cli.command()
@click.option("--gpu", "gpu_model", required=True,
              help="e.g. RTX_4090, H100_SXM, A100_SXM")
@click.option("--num-gpus", default=1, type=int)
@click.option("--image", default="pytorch/pytorch")
@click.option("--max-hours", default=4.0, type=float,
              help="Used to pre-check your balance can cover a run of this length.")
def run(gpu_model: str, num_gpus: int, image: str, max_hours: float):
    """Find, verify, and reserve the cheapest available GPU, then print
    connection details. Ghost-inventory and throttled-card candidates are
    silently skipped -- what you get back has already passed a live boot
    benchmark.

    Example: cloudweaver run --gpu RTX_4090
    """
    click.echo(f"Searching for {gpu_model} x{num_gpus}, verifying "
               f"availability and running boot benchmark (this can take "
               f"30-90s)...")
    start = time.time()
    resp = _api("POST", "/jobs/run", json={
        "gpu_model": gpu_model, "num_gpus": num_gpus,
        "image": image, "max_hours": max_hours,
    })
    data = resp.json()
    elapsed = time.time() - start

    click.echo(f"\nReserved in {elapsed:.0f}s:")
    click.echo(f"  Provider:    {data['provider']}")
    click.echo(f"  Price:       ${data['price_per_hour']:.3f}/hr")
    click.echo(f"  Benchmark:   {data['benchmark']['tflops']:.1f} TFLOPS, "
               f"{data['benchmark']['power_watts']:.0f}W (verified, not just advertised)")
    click.echo(f"  SSH:         ssh root@{data['ssh_host']}")
    click.echo(f"  Job ID:      {data['job_id']}")


@cli.command()
def jobs():
    """List your recent jobs and their cost."""
    resp = _api("GET", "/jobs")
    for job in resp.json()["jobs"]:
        warning = "  ⚠ balance low -- run `cloudweaver add-funds`" \
            if job.get("low_balance_warning") else ""
        click.echo(f"{job['id'][:8]}  {job['provider']:12}  "
                   f"{job['gpu_model']:10}  ${job['price_per_hour']:.3f}/hr  "
                   f"{job['status']}{warning}")


if __name__ == "__main__":
    cli()
