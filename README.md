# GPU Broker

Multi-cloud GPU rental broker: finds the cheapest GPU across 5 providers,
*actually verifies it's real and unthrottled before billing you for it*,
and gets it to you through a one-command CLI.

## Why this exists

Free price-comparison directories (gputable.dev, cheap-gpus.com, etc.) show
you a scraped price and stop there. Two real problems that leaves on the
table, both raised by actual practitioners replying to one of these
directories on Twitter:

1. **Ghost inventory** — a listed price/provider that isn't actually
   bookable when you try to rent it.
2. **Misrepresented hardware** — a GPU that's the right model on paper but
   power-capped or throttled, delivering less than advertised.

This project's entire value proposition is solving both *before* a
customer is ever charged: every reservation attempt is a live probe (if it
fails, we silently try the next-cheapest candidate), and every instance
gets a 30-60 second boot-time benchmark (real power draw + a quick matmul)
before it's handed over. See `backend/core/broker.py` and
`backend/core/benchmark.py`.

## Structure

```
backend/            FastAPI service — deploy this to Render
  providers/         One adapter per GPU provider (vast, runpod,
                      lambda_labs, crusoe, digitalocean), common
                      interface in base.py
  core/
    broker.py         Probe -> reserve -> benchmark -> fallback chain
    benchmark.py       Boot-time power/throughput verification
    wallet.py         Stripe + Supabase prepaid wallet logic
  db/schema.sql       Supabase Postgres schema
  main.py             API endpoints the CLI talks to
  config.py           Env-var-driven settings

cli/                 pip-installable CLI — the entire customer-facing
                      product surface (no dashboard, no website)
  gpu_deploy_cli/cli.py   login / add-funds / balance / run / jobs

BUILD_SPEC.md        Everything needed to take this from written code to
                      a live, running service: every account to create,
                      every env var, every TODO, in the order to do them.
                      Start here.
```

## Quick start (local dev, once accounts/keys exist)

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in real values, see BUILD_SPEC.md section 2
uvicorn main:app --reload

# separate terminal
cd cli
pip install -e .
gpu-deploy login --backend-url http://localhost:8000
gpu-deploy add-funds 20
gpu-deploy run --gpu RTX_4090
```

## Status

Freshly written against current provider documentation, cross-checked
against SkyPilot's own vendored provider code where available (both
SkyPilot and ec2instances.info's scraper were provided as reference and
used to validate real API patterns — see BUILD_SPEC.md §4 for adapter
confidence levels). Nothing has run against live accounts yet. Read
BUILD_SPEC.md before deploying anything.
