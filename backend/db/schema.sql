-- GPU broker schema. Run this in the Supabase SQL editor for a new project.
-- Uses Postgres functions for wallet credit/debit so balance changes are
-- atomic and ledgered together -- never update wallets.balance_usd
-- directly from application code.

create table users (
    id uuid primary key default gen_random_uuid(),
    api_key_hash text unique not null,       -- store a hash, never the raw key
    email text unique not null,
    stripe_customer_id text,
    stripe_payment_method_id text,
    auto_reload_enabled boolean not null default false,
    created_at timestamptz not null default now()
);

create table wallets (
    user_id uuid primary key references users(id),
    balance_usd numeric(10, 4) not null default 0
);

create table ledger_entries (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id),
    amount_usd numeric(10, 4) not null,       -- positive = credit, negative = debit
    kind text not null,                       -- 'stripe_topup' | 'job_charge' | 'auto_reload'
    stripe_session_id text,
    job_id uuid,
    created_at timestamptz not null default now()
);

create table jobs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references users(id),
    provider text not null,                   -- 'vast' | 'runpod' | 'lambda_labs' | 'crusoe' | 'digitalocean'
    provider_instance_id text not null,
    gpu_model text not null,
    price_per_hour numeric(10, 4) not null,   -- the CUSTOMER price locked at reservation time
    provider_cost_per_hour numeric(10, 4) not null,  -- what we actually paid -- for margin analysis
    benchmark_power_watts numeric(6, 1),
    benchmark_tflops numeric(6, 2),
    max_hours numeric(10, 4) not null default 4,     -- customer's requested max runtime (metering stop)
    status text not null default 'running',   -- 'running' | 'completed' | 'terminated_no_balance' | 'failed'
    started_at timestamptz not null default now(),
    last_metered_at timestamptz not null default now(),  -- end of last billed interval
    ended_at timestamptz
);

create index jobs_status_idx on jobs (status);

-- Provider reliability scoring -- this is the reputation system from the
-- "score providers on real outcomes" step. Update these counters every
-- time quote_and_reserve() succeeds or fails on a candidate.
create table provider_outcomes (
    id uuid primary key default gen_random_uuid(),
    provider text not null,
    gpu_model text not null,
    outcome text not null,     -- 'reserved_ok' | 'ghost_inventory' | 'benchmark_failed' | 'provider_error'
    created_at timestamptz not null default now()
);

create or replace function credit_wallet(
    p_user_id uuid, p_amount numeric, p_stripe_session_id text
) returns void as $$
begin
    insert into wallets (user_id, balance_usd) values (p_user_id, p_amount)
    on conflict (user_id) do update set balance_usd = wallets.balance_usd + p_amount;

    insert into ledger_entries (user_id, amount_usd, kind, stripe_session_id)
    values (p_user_id, p_amount, 'stripe_topup', p_stripe_session_id);
end;
$$ language plpgsql;

create or replace function debit_wallet(
    p_user_id uuid, p_amount numeric, p_job_id uuid
) returns void as $$
begin
    update wallets set balance_usd = balance_usd - p_amount where user_id = p_user_id;

    insert into ledger_entries (user_id, amount_usd, kind, job_id)
    values (p_user_id, -p_amount, 'job_charge', p_job_id);
end;
$$ language plpgsql;

-- Row-level security: OpenHands must enable RLS and add policies so a
-- user can only read their own wallet/jobs/ledger rows via the anon key.
-- The service-role key (used by the backend in core/wallet.py) bypasses
-- RLS by design -- never expose the service-role key to the CLI or any
-- client, only the backend service holds it.
alter table wallets enable row level security;
alter table jobs enable row level security;
alter table ledger_entries enable row level security;
