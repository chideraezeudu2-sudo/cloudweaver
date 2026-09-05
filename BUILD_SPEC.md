# GPU Broker — Build Spec for OpenHands

Owner (Francis) holds every account and API key. This document is everything
needed to take the code in `backend/` and `cli/` from "written against
documented APIs" to "actually running against live accounts." Nothing in
here has been tested against a real Vast.ai/RunPod/Stripe/Supabase account
— Claude wrote this code from current provider documentation but has no
network access to those services, so budget real testing time.

Read this top to bottom before touching anything. Sections are ordered in
the sequence you should actually do them in.

---

## 0. What already exists

- `backend/` — FastAPI service. `providers/` has one adapter per GPU
  provider (Vast.ai, RunPod, Lambda Labs, Crusoe, DigitalOcean), all behind
  a common interface in `providers/base.py`. `core/broker.py` is the
  probe→reserve→benchmark→fallback state machine. `core/wallet.py` is the
  Stripe/Supabase billing layer. `db/schema.sql` is the Postgres schema.
- `cli/` — the entire customer-facing product. `gpu-deploy login`,
  `add-funds`, `balance`, `run`, `jobs`. No dashboard, no website — that's
  intentional, not a gap.

## 1. Accounts to create (Francis does this — an agent cannot)

Create these in order; some need the others to exist first (e.g. Supabase
before you can wire the webhook).

1. **Supabase** — supabase.com, new project. Note the project URL and the
   `service_role` key (Settings → API). Run `backend/db/schema.sql` in the
   SQL editor.
2. **Stripe** — dashboard.stripe.com. Get the secret key (test mode first).
   Add a webhook endpoint pointing at `<your-render-url>/stripe/webhook`
   subscribed to `checkout.session.completed`; copy the signing secret.
3. **Vast.ai** — vast.ai/console/cli/ for the API key. `pip install vastai`
   locally to confirm the key works before deploying:
   `vastai search offers 'gpu_name=RTX_4090'`
4. **RunPod** — runpod.io console → Settings → API Keys.
5. **Lambda Labs** — cloud.lambda.ai → API keys. **Also required**: upload
   an SSH public key in the console first (Lambda instances only launch
   with a key name already registered there — this can't be done via the
   launch API call itself). Note the exact key name you gave it; it goes
   in `LAMBDA_SSH_KEY_NAME`.
6. **Crusoe Cloud** — console.crusoecloud.com → Access Keys. Note: this is
   the least finished adapter (see §4 below) — get the account created
   now, but don't block the rest of the launch on it.
7. **DigitalOcean** — cloud.digitalocean.com → API → generate a token with
   read+write scope. Also upload an SSH key under Settings → Security and
   note its numeric ID (`DO_SSH_KEY_ID`) — same pattern as Lambda.
8. **Broker SSH keypair** — generate ONE keypair the broker itself uses to
   access every instance it provisions, regardless of provider:
   `ssh-keygen -t ed25519 -f broker_key -N ""`. The public key goes in env
   var `BROKER_SSH_PUBLIC_KEY`, the private key path in
   `BROKER_SSH_PRIVATE_KEY_PATH` (upload the private key file itself to
   Render as a secret file, not an env var, since it's multi-line).
9. **Render** — new Web Service, connect the GitHub repo, root directory
   `backend/`, build command `pip install -r requirements.txt`, start
   command `uvicorn main:app --host 0.0.0.0 --port $PORT`.
10. **PyPI** — pypi.org account, needed to publish the CLI in §6.
11. **GitHub repo** — push this code here; Render deploys from it.

## 2. Environment variables (set these on Render, and locally in `.env`
   for testing — `backend/config.py` already reads them via pydantic-settings)

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
VAST_API_KEY=
RUNPOD_API_KEY=
LAMBDA_API_KEY=
LAMBDA_SSH_KEY_NAME=
CRUSOE_ACCESS_KEY=
CRUSOE_SECRET_KEY=
CRUSOE_PROJECT_ID=
DO_API_TOKEN=
DO_SSH_KEY_ID=
BROKER_SSH_PUBLIC_KEY=
BROKER_SSH_PRIVATE_KEY_PATH=/etc/secrets/broker_key   (Render secret file path)
```

## 3. Things the code deliberately left as TODOs — finish these before
   any real customer touches it

- **`main.py` → `get_user_id()`**: currently raises `NotImplementedError`.
  Needs: hash the incoming bearer token, look it up against
  `users.api_key_hash` in Supabase, return the matched `user_id`. Generate
  real API keys for users at signup (a random 32-byte token, store only
  its hash, show the raw value to the user exactly once).
- **`main.py` → `/jobs/run`**: after `quote_and_reserve()` succeeds, persist
  a row to the `jobs` table and start a metering loop. The metering loop
  itself isn't written — see §5.
- **`main.py` → `list_jobs()`**: query the `jobs` table, not implemented.
- **Signup flow**: there's no `/signup` endpoint at all yet. Simplest v1:
  a `POST /signup {email}` that creates a `users` row, generates an API
  key, emails it or returns it directly in the response (fine for a v1
  aimed at developers who'll pipe it straight into `gpu-deploy login`).

## 4. Provider adapters — confirm against live accounts before trusting them

Every adapter in `backend/providers/` was written against each provider's
current public documentation, cross-checked against SkyPilot's own vendored
adapter code (`sky/provision/vast/utils.py` confirms the `vastai` package
usage pattern) where available. None have been run against a live account.
Test each one individually before wiring them all into the broker:

- **`vast.py`** — highest confidence; matches SkyPilot's production usage
  of the same `vastai` SDK. Test: `VastAdapter().search_offers("RTX_4090")`.
- **`runpod.py`** — GraphQL, confirmed against RunPod's docs. **Check**:
  RunPod shipped a REST API v2 in beta mid-2026 — if it's GA by the time
  you build this, prefer it (simpler bearer-token auth) and update this
  adapter; the `Offer`/`Instance` shape returned to the broker doesn't
  need to change either way.
- **`lambda_labs.py`** — medium confidence, Basic auth confirmed via docs.
  No spot tier — this will basically never be your cheapest option, it's
  a reliability fallback.
- **`crusoe.py`** — **NOT FUNCTIONAL AS WRITTEN.** Crusoe signs requests
  with HMAC-SHA256, not a bearer token, and `_request()` deliberately
  raises `NotImplementedError` rather than pretend to work. Read
  https://docs.crusoecloud.com/api/ for the actual signing scheme and
  implement it, or deprioritize Crusoe for launch — it's 1 of 5 providers,
  the broker degrades gracefully without it (see `registry.py`, a provider
  that fails to construct is just excluded).
- **`digitalocean.py`** — medium confidence. GPU Droplet size slugs
  (`gpu-h100x1-80gb` etc.) are a guess based on DO's naming convention —
  confirm real current slugs via `GET /v2/sizes` against your own account
  before relying on them.

## 5. The job metering loop (not written — this needs real infra decisions)

`core/wallet.py`'s `meter_job_usage()` exists but nothing calls it on a
schedule yet. Options, roughly in order of how much infra they need:

- **Simplest**: a Render Cron Job that runs every 5 minutes, queries all
  `jobs` where `status = 'running'`, calls `meter_job_usage()` for each,
  and calls the relevant provider adapter's `destroy_instance()` +
  updates `jobs.status` if `InsufficientBalance` is raised or
  `max_hours` is exceeded.
- **More responsive**: a long-running background worker process (separate
  Render service) instead of a 5-minute cron, if you want faster reaction
  to a depleted balance.

Either way: **never let a job run un-metered for more than a few minutes**
— that's the gap where you'd eat a loss if a customer's balance runs out
mid-job.

## 6. Publishing the CLI

```
cd cli
pip install build twine
python -m build
twine upload dist/*
```

After that, anyone can `pip install gpu-deploy` — confirm the package name
isn't already taken on PyPI before this step (likely needs a rename;
`gpu-deploy` is a common enough phrase that it may collide).

## 7. Testing checklist before any real customer runs a job

- [ ] Run `POST /jobs/run` against Vast.ai alone (temporarily disable other
      adapters in `registry.py`) and confirm an SSH-reachable instance
      actually comes back.
- [ ] Deliberately request a GPU model/region combination you know has no
      capacity, and confirm the broker falls back / raises
      `NoCapacityAvailable` cleanly instead of hanging or crashing.
- [ ] Confirm the boot benchmark actually runs and its numbers look sane
      for a real card (compare against published specs for that GPU).
- [ ] Run the full payment loop end-to-end in Stripe **test mode**: add
      funds, confirm the webhook credits the wallet, run a job, confirm
      `meter_job_usage` debits it correctly.
- [ ] Deliberately drain a test wallet to near-zero mid-job and confirm
      the metering loop terminates the instance rather than let it run
      unbilled.
- [ ] Confirm `destroy_instance()` is actually idempotent for every
      provider (call it twice, second call shouldn't error) — the broker's
      fallback path depends on this.

## 8. Spot preemption: what's handled now vs. deferred

Interruptible/spot capacity (what makes the cheap tier cheap) can be
reclaimed by the provider for a higher bidder at any moment. Three-stage
plan, only stage 1 is built:

**Stage 1 (DONE, this commit)** -- detect + don't overbill. The metering
loop now checks the instance is actually still alive on the provider's
side before billing each interval (`core/metering.py`). If the provider
reports it gone, the job is marked `terminated_preempted` and billing
simply stops -- the customer is never charged for compute they didn't
get. This was a deliberate business decision, not just a technical one:
billing for preempted time is what turns an infrastructure hiccup into a
Paddle chargeback.

**Stage 2 (documented convention, not yet enforced in code)** -- customers
who want resumable long-running jobs should have their script periodically
write progress to `/checkpoint` inside the instance. This directory isn't
currently backed by anything special -- it's a convention being
established now so Stage 3 doesn't require customers to change their
scripts later. Document this in the CLI's `run` command help text once
Stage 3 exists; no code change needed until then.

**Stage 3 (future, not started)** -- on detecting preemption, instead of
just terminating, copy `/checkpoint`'s contents somewhere durable
(off-instance, since the dead machine may be unreachable), reserve a new
instance via the normal broker fallback chain, restore `/checkpoint`
there, and resume the customer's job. This only works for jobs whose own
code actually writes to `/checkpoint` -- it can't magically save an
arbitrary program's progress, same limitation SkyPilot has. Needs Stage 1
proven in production first.

## 9. Explicitly out of scope for v1 (do not build these yet)

- Any web dashboard or frontend — Stripe Checkout's hosted page covers
  fund-adding, the CLI covers everything else.
- The SEO cost-comparison calculator, comparison landing pages, or any of
  the marketing-site ideas from the original pitch doc — those are
  post-traction, not pre-launch.
- Support for more than the 5 providers above.
- Stage 3 checkpoint/auto-resume from section 8 above — that's a real
  gap for long training runs; scope it as a fast-follow once Stage 1 is
  proven in production, not before.
