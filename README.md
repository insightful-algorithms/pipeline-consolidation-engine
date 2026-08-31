# Pipeline Consolidation Engine

[![Pipeline Consolidation CI](https://github.com/insightful-algorithms/pipeline-consolidation-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/insightful-algorithms/pipeline-consolidation-engine/actions/workflows/ci.yml)

A pipeline that pulls together UK government debt and financial hardship data from four different publishers, and puts it all into one clean, queryable format.

Built with Python, PyYAML, SQLite, and Apache Airflow. Gold-layer star schema built in plain SQL after a documented Spark/Delta Lake environment issue on Windows. Azure Databricks and Power BI are next.

---

## The Problem

UK government debt data is published by four separate bodies: the Food Standards Agency, the Insolvency Service, Ofgem, and the Office for National Statistics. Each one publishes on its own schedule, in its own file format, with its own column names. There is no single place to see all of this data together.

Right now, if you wanted a full picture, you would have to visit four different websites, download four different file types, and piece it together by hand.

This project fixes that. It pulls real files from all four sources, checks them properly, and loads them into one shared, consistent table. It also catches duplicate data automatically, and it catches when a publisher quietly revises an old figure.

---

## Why This Project Is Different

**Every file is real.** Nothing here is made up. About 155 files were checked by hand before deciding which were worth keeping. Every decision to keep or drop a file is backed by something I actually checked, not a guess.

**Revision detection actually works, and I proved it.** I found, by hand, a figure from the Insolvency Service that had quietly changed between two releases. Once the pipeline was built, it caught that exact same change on its own, plus hundreds more I had not found by hand, across three different sources.

**The design holds up across very different data.** Each new source I added broke an assumption the code had made for the source before it. Instead of patching around each problem, I changed the design so it could handle all of them properly. That includes a source shaped like one row per file, a source shaped like many small standalone indicators, and a source where one wide row had to be turned into many separate rows.

**Every claim in this README is backed by an automated test that runs on every push, on a machine I have never touched.** See the CI badge above.

---

## How It Works

```
Bronze (raw files, untouched)
   Real files from each publisher, checked and verified

        |
        v

Silver (cleaned and loaded)
   Each source has its own config file describing its shape.
   One shared engine reads the config and loads the data.

        |
        v

One shared table (SQLite for now)
   One row per publisher, indicator, place, and time period

        |
        v

Gold layer (done)
   A real star schema: one fact table, three dimension tables,
   including a dimension that tracks a real change in how ONS
   names its own reference tables over time.

        |
        v

Power BI dashboard (coming next)
```

---

## The Four Data Sources

| Source                | What it publishes                                                                 | Files kept | The tricky part                                                                                               |
| --------------------- | --------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| Food Standards Agency | Meat industry debtor days                                                         | 4 of 18    | Mixed CSV and Excel files, overlapping date ranges                                                            |
| Insolvency Service    | Bankruptcies, DROs, IVAs, plus Northern Ireland and an authorising-body breakdown | 12 of 100+ | Old figures get quietly revised over time. One table had to be turned from a wide layout into individual rows |
| Ofgem                 | Energy debt and arrears                                                           | 13 of 26   | Some files have no dates at all, just supplier names                                                          |
| ONS                   | Government deficit and debt, seven separate tables                                | 3 of 10    | One column mixes four different date formats. One table's own publisher renamed it partway through            |

---

## Key Decisions I Made

**Config files, not hardcoded scripts.** Adding a new data source means writing a config file, not new code. I proved this by adding several very different sources after the first one, without rewriting the core logic each time. One source needed a completely different loading strategy, since it is shaped as many small standalone indicators rather than a shared set of files. The engine detects which shape a config is and picks the right strategy automatically.

**No duplicate data, ever.** Every row gets a unique ID based on its publisher, indicator, place, and date. Running the pipeline twice never creates duplicates. I proved this directly: the old, naive way of loading FSA data created 48 rows when there should only be 32. The new way loads exactly 32, every single time.

**The Insolvency Service config was generated, not typed by hand.** It has 30 different indicators, and I wrote a script that reads the publisher's own metadata file and builds the config from it automatically.

**Old figures that change are tracked, not overwritten.** Before saving a new value, the pipeline checks what is already there. If a figure changed, it logs the old value, the new value, and where each one came from.

**No SQL injection risk.** Every value going into the database is passed in separately from the SQL command itself. The database can never mistake a piece of data for an instruction.

**The Gold layer tracks a real change in a publisher's own naming.** ONS renamed one of its reference tables partway through the period this project covers, and dropped a table of its own official revisions at the same time. The publisher dimension in the Gold layer records both versions properly, with the dates each one was actually in use.

**Orchestrated with Apache Airflow.** Every source loads through a scheduled, monitored task rather than being run by hand. The twelve sources are genuinely independent of each other, so they run in parallel rather than one after another.

---

## Project Structure

```
pipeline-consolidation-engine/
|-- bronze/                    Raw files, untouched
|   |-- fsa/
|   |-- insolvency_service/
|   |-- ofgem/
|   |-- ons/
|-- silver/
|   |-- schema.sql              Table definitions
|-- gold/
|   |-- build_gold.py            Builds the star schema from Silver
|-- warehouse/                  The database file (not stored in git)
|-- framework/
|   |-- config/
|   |   |-- sources/             One config file per data source
|   |   |-- environments/
|   |-- readers/                  Reads CSV and Excel files
|   |-- transformers/              Cleans and shapes the data
|   |-- loaders/                    Loads it into the database
|   |-- engine.py                    Runs the whole pipeline
|   |-- tests/                        Automated tests, one per source
|-- airflow/
|   |-- dags/                        The scheduled pipeline definition
|-- legacy/                     The old, naive scripts, kept on purpose
|                                to show exactly what problems they had
|-- docs/
|   |-- REQUIREMENTS.md
|   |-- SILVER_SCHEMA_DESIGN.md
|   |-- LEGACY_STATE.md
|-- .github/workflows/
    |-- ci.yml                       Runs every test on every push
```

---

## Getting Started

```bash
git clone https://github.com/insightful-algorithms/pipeline-consolidation-engine.git
cd pipeline-consolidation-engine

python -m venv venv
source venv/Scripts/activate   # Windows Git Bash
# source venv/bin/activate     # Mac or Linux

pip install -r requirements.txt
```

### Run one data source

```bash
python -m framework.engine
```

### Build the Gold layer

```bash
python gold/build_gold.py
```

### Run all the tests

```bash
python -m pytest framework/tests/ -v
```

### Run the full pipeline on a schedule

```bash
docker-compose up -d
```

Then open `http://localhost:8080` to see the Airflow UI.

---

## Proof, Not Just Claims

| What I claim                                 | How I proved it                                                                              |
| -------------------------------------------- | -------------------------------------------------------------------------------------------- |
| No duplicate rows                            | Automated test checks the exact row count for every source                                   |
| Revisions get caught, not lost               | Every load checks old values against new ones before saving                                  |
| Row counts are correct                       | Each source has a test with a known, correct number to check against                         |
| Data is real, not made up                    | Every file was checked by hand first. See docs/LEGACY_STATE.md                               |
| Tests genuinely pass, not just on my machine | Every push runs the full test suite on a fresh GitHub-hosted machine. See the CI badge above |

---

## What's Left To Do

- Confirm every Airflow task completes cleanly in a single run, not just most of them
- Connect Azure Databricks
- Build a Power BI dashboard on top of the finished Gold layer
- Add the remaining Insolvency Service data product (IVA cohort outcomes) and the two ONS tables not yet covered (M8R, discontinued mid-project)

---

## Author

**Ose Omokhua**
MSc Data Science, BSc Physics
London, UK

Open to Data Engineer and Data Scientist roles (UK and Remote)

[![GitHub](https://img.shields.io/badge/GitHub-insightful--algorithms-181717?style=flat&logo=github&logoColor=white)](https://github.com/insightful-algorithms)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/omokhua-ose)
