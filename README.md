DATA ENGINEERING-PROJECT-1 : STREAMING PIPELINE

# 📦 Real-Time E-Commerce Data Pipeline

A full end-to-end data engineering project — streaming ingestion, dimensional modeling, automated testing, orchestration, and a live dashboard. Built from scratch to understand how modern data platforms actually work, not just to follow a tutorial.

**🔗 Live Dashboard:** [de-project-1-streaming-pipeline-8obfg7ajzyt7ju6qtglqs3.streamlit.app](https://de-project-1-streaming-pipeline-8obfg7ajzyt7ju6qtglqs3.streamlit.app/)

---

## What this project does

Simulates a real e-commerce order stream and processes it through a production-style pipeline:

```
Fake order events (Python + Faker)
        ↓
Redpanda (Kafka-compatible message queue)
        ↓
Consumer → raw storage (Supabase / Postgres)
        ↓
dbt (staging → dimensional model → tests)
        ↓
Dagster (orchestration + scheduling)
        ↓
Streamlit dashboard (live, deployed)
```

Every layer is real — not mocked. Events genuinely flow through a message queue, land in a cloud-hosted Postgres database, get transformed through tested dbt models, and are orchestrated on a schedule, all visible on a live dashboard.

---

## Architecture

- **Ingestion:** A Python producer generates realistic fake order events (using a fixed pool of repeat customers, not random one-off names) and publishes them to a `orders` topic in Redpanda. A separate consumer reads from that topic and writes to a raw Postgres table, with duplicate-safe inserts.
- **Storage:** Supabase (managed cloud Postgres), accessed via the session connection pooler.
- **Transformation:** dbt models build a staging layer (cleaned raw data) and a proper dimensional model — `dim_customers` and `fct_orders` — following a star schema pattern. Every key column has automated `unique`/`not_null` tests.
- **Orchestration:** Dagster wraps the dbt project as native assets, with a scheduled job (cron: `0 2 * * *`) to run the pipeline automatically.
- **Dashboard:** A Streamlit app reads directly from the dbt marts and shows revenue, order counts, top customers, and recent order activity — deployed live on Streamlit Community Cloud.
- **Containerization:** Redpanda, the producer, and the consumer all run via a single `docker-compose up` command. dbt and Dagster currently run through a local virtual environment (see *Known limitations* below).

---

## Tech stack

Python · SQL · Docker · Redpanda (Kafka-compatible) · Postgres · Supabase · dbt · Dagster · Streamlit · Plotly

---

## Running it locally

**Prerequisites:** Docker Desktop, Python 3.12, a Supabase (or any Postgres) instance.

```bash
git clone https://github.com/ProteinAcid/de-project-1-streaming-pipeline.git
cd de-project-1-streaming-pipeline

# copy and fill in your own database credentials
cp .env.example .env

# start Redpanda, producer, and consumer
docker-compose up -d --build

# set up dbt (separately, using a venv)
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd de_project_transform
dbt run
dbt test

# run Dagster locally
cd ../dagster_project
dagster dev -f definitions.py

# run the dashboard
cd ..
streamlit run dashboard.py
```

---

## Known limitations (intentional, and I can explain the reasoning for each)

- **dbt and Dagster aren't containerized yet.** They currently run through a local venv rather than Docker, pinned to Python 3.12 specifically — I hit real dependency conflicts trying to run them on Python 3.14 (see below) and prioritized getting the ingestion layer and dashboard fully shipped first.
- **The producer/consumer run as always-on containers, separate from Dagster's scheduled orchestration.** This is a deliberate design choice, not an oversight — they represent a continuous streaming ingestion layer, while Dagster handles scheduled batch transformation. In real systems, these are often genuinely different tools solving different problems, not one replacing the other.
- **No AI/agent layer in this version.** Originally scoped as an optional later addition — I'm building agent/LLM patterns properly in a second project first, then plan to bring a lightweight version (e.g. an automated anomaly-check step) back into this pipeline.

---

## Real problems I ran into (and actually solved, not just papered over)

I kept a running decisions log throughout the build (`decisions.md`) — a few of the more interesting ones:

- **Python version compatibility:** Built the whole environment on Python 3.14 initially, which caused cascading dependency conflicts with Dagster's dbt integration (most releases at the time capped support below 3.14). Diagnosed it back to the actual root cause instead of switching tools, and rebuilt the environment on Python 3.12 via the deadsnakes PPA.
- **Docker networking:** Once I containerized the producer/consumer, they couldn't reach Redpanda — because Redpanda's advertised address was still `localhost`, which inside a container just points back at itself. Fixed by configuring Redpanda with separate internal (`redpanda:9092`) and external (`localhost:19092`) listeners.
- **A startup race condition:** Producer/consumer containers sometimes started before Redpanda was actually ready to accept connections, even though Docker considered it "started." Fixed with a proper Docker healthcheck instead of just `depends_on`.
- **Inconsistent secret escaping:** My database password contained a `$`, which Docker Compose and `python-dotenv` interpret completely differently — one needed `$$` to escape it, the other needed a single `$`. Same secret, two different correct formats depending on which tool was reading it.
- **A silently broken dbt model:** An automated dbt test caught a wrong table alias (`o.customer_id` instead of `c.customer_id`) in my fact table — data that would have silently shipped as broken `customer_id` values if I hadn't had tests in place.

Full details on all of these (and more) are in `decisions.md`.

---

## What I'd do differently / next steps

- Containerize dbt and Dagster fully, so the entire stack runs from one `docker-compose up`
- Add a data freshness/anomaly-check asset in Dagster
- Layer in an AI agent step once I've built that pattern properly in Project 2

---

*Built as part of a self-directed data engineering learning roadmap — this was my first hands-on project with Kafka-style streaming, dbt, and Dagster, built from scratch with a focus on actually understanding each layer, not just getting it to run.*