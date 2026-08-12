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

## Phase 4 — Orchestration (Dagster)

**Decision:** Used Dagster over Airflow for orchestration
**Why:** Asset-based mental model maps naturally onto an existing dbt project (models are already "assets"); lighter local setup than Airflow; growing real-world adoption; differentiates from the majority of portfolio projects that default to Airflow.

**Decision:** Wrapped existing dbt project as Dagster assets via dagster-dbt integration
**Why:** Avoids duplicating transformation logic in two places — Dagster orchestrates the existing dbt models directly rather than reimplementing them.

**Major debugging incident:** Initial Dagster + dagster-dbt install failed with cascading dependency conflicts. Root cause: project's Python version (3.14) was too new — most current dagster-dbt releases require Python <3.14. Fixed by installing Python 3.12 via the deadsnakes PPA and rebuilding the virtual environment. Lesson: verify a tool's supported Python version range before adopting a brand-new Python release for a new project, especially with fast-moving/smaller ecosystem libraries.

**Secondary issue:** DbtCliResource and DbtProject each independently need an explicit `profiles_dir` pointed at `~/.dbt` (where profiles.yml lives, outside the dbt project folder by dbt convention) — passing it to only one of the two objects still fails, since dbt-project-loading and dbt-CLI-execution are validated separately.

**Decision:** Added a scheduled job (de_project_job) running via cron_schedule "0 2 * * *"
**Why:** Automates the pipeline to run nightly without manual intervention — the actual point of orchestration versus manually clicking "Materialize." Chose 2 AM as a placeholder time simulating a typical "run after the day's data has landed" pattern real companies use.

**Architecture note:** producer.py and consumer.py remain separate, continuously-running processes outside Dagster's scheduled orchestration, rather than being wrapped as Dagster assets. This is a deliberate choice: they represent an always-on streaming ingestion layer, while Dagster is used for scheduled batch transformation (dbt). Real systems commonly separate these concerns — a streaming ingestion layer and a batch orchestrator are different tools solving different problems, not one replacing the other.

## Phase 6 — Containerization

**Decision:** Containerized producer/consumer alongside existing Postgres/Redpanda services
**Why:** Enables the entire ingestion stack to start with a single `docker-compose up` command — critical for reproducibility and for anyone (including an interviewer) to run the project without manual multi-step setup.

**Decision:** Used environment variables (.env + python-dotenv) instead of hardcoded connection strings
**Why:** Same code now works whether run directly via venv (localhost) or inside Docker (service names like `redpanda`/`postgres`) — addresses the hardcoded-credentials gap noted back in Phase 1.

**Bug 1 — Docker networking:** Initial container-to-container connection failed because Redpanda's advertised address was still `localhost`, which inside a container refers to itself, not the Redpanda container. Fixed by configuring Redpanda with dual listeners — an internal `PLAINTEXT` listener advertised as `redpanda:9092` for other containers, and a separate `OUTSIDE` listener on port 19092 for host-machine access.

**Bug 2 — dependency packaging:** `kafka-python==2.0.2` failed inside the container with a broken internal `six` import, even after explicitly installing `six`. Root cause was a known packaging issue in that specific release. Resolved by switching to `kafka-python-ng`, an actively maintained, API-compatible fork — required zero changes to actual application code.

**Bug 3 — race condition on startup:** producer/consumer initially failed with `NoBrokersAvailable` because Docker's `depends_on` only waits for a container to *start*, not to be *ready* — Redpanda's container reported as started before it could actually accept client connections. Fixed by adding a proper Docker healthcheck (`rpk cluster health`) to the Redpanda service and updating `depends_on` to wait on `condition: service_healthy` rather than just container start.

**Lesson:** Three genuinely different failure categories in one containerization pass — networking/addressing, dependency packaging, and startup ordering/race conditions. All three are common, real production issues, not beginner mistakes — good, legitimate debugging material for interviews.

## Phase 6 — Dashboard (Streamlit)

**Decision:** Built dashboard using Streamlit + Plotly, reading directly from dbt marts (fct_orders, dim_customers)
**Why:** Pure Python (no JS needed), free to deploy, and reads from the same trusted, tested transformation layer rather than querying raw data directly — dashboard reflects the same business logic used everywhere else in the pipeline.

**Bug found via dashboard, not code review:** Initial dashboard revealed Total Orders == Unique Customers exactly, exposing that the producer's fake data generation didn't simulate repeat customers (a fresh random name was generated per order instead of sampling from a fixed customer pool). This is a good example of a data quality issue surfaced through downstream visualization rather than upstream testing — fixed by having the producer generate a fixed pool of 50 customer names once at startup and sample from it per order, better simulating realistic repeat-customer behavior.

## Phase 6 — Migration to Supabase (managed cloud Postgres)

**Decision:** Migrated from local Docker Postgres to Supabase (managed cloud Postgres)
**Why:** Enables a genuinely live, publicly deployable dashboard — Streamlit Cloud can't reach a database running on a local machine. Also more realistic: production systems point at managed databases, not developer laptops.

**Bug 1 — DNS resolution failure:** Direct Supabase connection host failed inside Docker containers with "could not translate host name," due to the direct-connection hostname being IPv6-only in this environment, which Docker's default networking couldn't resolve. Fixed by switching to Supabase's Session Pooler connection (IPv4-compatible, different host/port, username format changes to `postgres.<project-ref>`).

**Bug 2 — inconsistent secret escaping across tools:** The database password contained a `$` character, which has different special meanings depending on which tool reads it: Docker Compose requires `$$` to escape a literal `$` in both `.env` files and inline YAML values, while `python-dotenv` (used directly by Python scripts/dashboard) does NOT use this convention and reads `$` literally. Using the same escaped value in both places caused one tool to authenticate successfully while the other failed. Resolved by using single `$` in `.env` (read by python-dotenv) and `$$` only where Docker Compose parses the same secret inline in docker-compose.yml. Lesson: the same secret can require different escaping depending on the consuming tool — worth verifying per-tool rather than assuming one universal format.