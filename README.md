# Cloud Weaver

Multi-cloud GPU rental broker: finds the cheapest GPU across marketplaces,
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

Cloud Weaver's entire value proposition is solving both *before* a
customer is ever charged: every reservation attempt is a live probe (if it
fails, we silently try the next-cheapest candidate), and every instance
gets a boot-time benchmark (real power draw + a quick matmul) before it's
handed over. See `backend/core/broker.py` and `backend/core/benchmark.py`.

A third layer, added after launch testing: the metering loop also checks
an instance is still genuinely alive on the provider's side before billing
each interval, so spot preemption (the provider reclaiming a cheap card for
a higher bidder) stops billing immediately instead of quietly overcharging
for compute that got pulled out from under the customer. See
`backend/core/metering.py` and BUILD_SPEC.md §8.

## Structure

```
backend/            FastAPI service — deployed on Render
  providers/         One adapter per GPU provider. LAUNCH SCOPE: only
                      vast.py + runpod.py are active (see registry.py) --
                      lambda_labs/crusoe/digitalocean exist but are
                      deliberately not wired in yet (need funded
                      accounts / unfinished auth scheme), common
                      interface in base.py
  core/
    broker.py         Probe -> reserve -> benchmark -> fallback chain
    benchmark.py       Boot-time power/throughput verification
    metering.py       Per-interval billing + preemption detection
    wallet.py         Paddle + Supabase prepaid wallet logic (fixed
                      $5/10/20/50/100 top-up tiers, no freeform amount --
                      Paddle's catalog model, not Stripe's)
  db/schema.sql       Supabase Postgres schema
  main.py             API endpoints the CLI talks to, incl. /pay (the
                      Paddle.js checkout page) and /paddle/webhook
  config.py           Env-var-driven settings

cli/                 pip-installable CLI — the entire customer-facing
                      product surface (no dashboard, no website)
  cloudweaver_cli/cli.py   login / add-funds / balance / run / jobs

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
cloudweaver login --backend-url http://localhost:8000
cloudweaver add-funds 20
cloudweaver run --gpu RTX_4090
```

## Status

Live in production (Vast.ai + RunPod, Paddle sandbox), with a real
end-to-end payment flow proven end to end: real checkout, real card
payment, real webhook delivery, and confirmed idempotency (a duplicate
webhook delivery does not double-credit a wallet). Not yet live on
Paddle's production/live environment -- see BUILD_SPEC.md for what that
transition needs.

Known open gap: spot-preemption auto-resume (checkpoint a job's progress
and automatically continue it on a new instance) is deliberately not
built yet -- see BUILD_SPEC.md §8 for the staged plan.
