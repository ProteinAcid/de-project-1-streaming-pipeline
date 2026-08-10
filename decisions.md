# Project Decisions Log

## Phase 0 — Environment Setup

**Decision:** Used WSL2 + Docker instead of native Windows tools
**Why:** Most data engineering tools (Kafka/Redpanda, Airflow/Dagster, dbt) are built assuming a Linux environment. WSL2 gives Linux-parity locally, matching what production systems actually run on.

**Decision:** Containerized Postgres via Docker instead of installing it natively on Windows
**Why:** Keeps the environment reproducible and isolated — the whole stack can be torn down and rebuilt with one command (`docker-compose up`), and it mirrors how databases are typically run in real deployments.

**Decision:** Used GitHub CLI (`gh`) instead of manual token-based HTTPS auth
**Why:** Simpler authentication flow, avoids storing raw tokens manually in Git remote URLs.

## Phase 1 — Ingestion Layer

**Decision:** Used Redpanda instead of Apache Kafka
**Why:** Same wire-protocol compatibility as Kafka, but lighter to run locally (no JVM/Zookeeper dependency), while still being a legitimate production-grade choice used by real companies.

**Decision:** Used `auto_offset_reset='earliest'` for the consumer
**Why:** This pipeline needs completeness — no event should be silently skipped, even if the consumer starts after the producer has already been running. Verified this behavior by manually stopping the consumer, letting the producer run alone, then confirming all events were picked up on restart.

**Decision:** Used `ON CONFLICT (order_id) DO NOTHING` on insert
**Why:** Protects against duplicate processing if the consumer ever re-reads an event (e.g., if it crashes after inserting but before committing its offset) — makes the insert operation idempotent (safe to run more than once on the same data).

**Known gap:** Postgres password is currently hardcoded in scripts rather than loaded from an environment variable / `.env` file. Acceptable for local learning project, but would need fixing (using `.env` + `python-dotenv`) before this pattern is used anywhere real. Will address if time permits.

## Phase 2 — Transformation Layer (dbt)

**Decision:** Organized models into staging/ and marts/ folders
**Why:** Standard dbt convention — staging holds cleaned 1:1 versions of raw sources, marts holds final business-ready tables. Keeps transformation logic layered and avoids repeating cleanup logic across multiple downstream tables.

**Decision:** Built a basic dimensional model (dim_customers, fct_orders) instead of one flat table
**Why:** Demonstrates star schema pattern — fact table stores transactions/measurements, dimension table stores descriptive attributes, joined via a surrogate key (customer_id) instead of repeating customer_name in every row.

**Decision:** Used dbt's built-in schema tests (unique, not_null) on key columns
**Why:** Automates data quality validation instead of manual spot-checking — catches broken joins or malformed data immediately (caught a real bug this way: an incorrect table alias in fct_orders that silently would've shipped a broken customer_id column if untested).

**Bug caught during build:** fct_orders initially referenced `o.customer_id` (wrong table alias) instead of `c.customer_id` — dbt test failures on the fact table surfaced this immediately rather than it silently shipping broken data. Good real example of why testing matters.