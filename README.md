# Pipeline Consolidation Engine

A pipeline that pulls together UK government debt and financial hardship data from four different publishers, and puts it all into one clean, queryable format.

Built with Python, PyYAML, and SQLite. Moving to Spark and Delta Lake on Azure Databricks next.

---

## The Problem

UK government debt data is published by four separate bodies: the Food Standards Agency, the Insolvency Service, Ofgem, and the Office for National Statistics. Each one publishes on its own schedule, in its own file format, with its own column names. There is no single place to see all of this data together.

Right now, if you wanted a full picture, you would have to visit four different websites, download four different file types, and piece it together by hand.

This project fixes that. It pulls real files from all four sources, checks them properly, and loads them into one shared, consistent table. It also catches duplicate data automatically, and it catches when a publisher quietly revises an old figure.

---

## Why This Project Is Different

**Every file is real.** Nothing here is made up. About 155 files were checked by hand before deciding which 32 were worth keeping. Every decision to keep or drop a file is backed by something I actually checked, not a guess.

**Revision detection actually works, and I proved it.** I found, by hand, a figure from the Insolvency Service that had quietly changed between two releases. Once the pipeline was built, it caught that exact same change on its own, plus hundreds more I had not found by hand.

**The design holds up across very different data.** Each new source I added broke an assumption the code had made for the source before it. Instead of patching around each problem, I changed the design so it could handle all of them properly.

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

One shared table (SQLite for now, moving to Delta Lake)
   One row per publisher, indicator, place, and time period

        |
        v

Gold layer and Power BI dashboard (coming next)
```

---

## The Four Data Sources

| Source                | What it publishes                      | Files kept | The tricky part                                      |
| --------------------- | -------------------------------------- | ---------- | ---------------------------------------------------- |
| Food Standards Agency | Meat industry debtor days              | 4 of 18    | Mixed CSV and Excel files, overlapping date ranges   |
| Insolvency Service    | Bankruptcies, debt relief orders, IVAs | 12 of 100  | Old figures get quietly revised over time            |
| Ofgem                 | Energy debt and arrears                | 13 of 26   | Some files have no dates at all, just supplier names |
| ONS                   | Government deficit and debt            | 3 of 10    | One column mixes four different date formats         |

---

## Key Decisions I Made

**Config files, not hardcoded scripts.** Adding a new data source means writing a config file, not new code. I proved this works by adding three very different sources after the first one, without rewriting the core logic each time.

**No duplicate data, ever.** Every row gets a unique ID based on its publisher, indicator, place, and date. Running the pipeline twice never creates duplicates. I proved this directly: the old, naive way of loading FSA data created 48 rows when there should only be 32. The new way loads exactly 32, every single time.

**The Insolvency Service config was generated, not typed by hand.** It has 30 different indicators, and I wrote a script that reads the publisher's own metadata file and builds the config from it automatically.

**Old figures that change are tracked, not overwritten.** Before saving a new value, the pipeline checks what is already there. If a figure changed, it logs the old value, the new value, and where each one came from.

**No SQL injection risk.** Every value going into the database is passed in separately from the SQL command itself. The database can never mistake a piece of data for an instruction.

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
|-- legacy/                     The old, naive scripts, kept on purpose
|                                to show exactly what problems they had
|-- docs/
    |-- REQUIREMENTS.md
    |-- SILVER_SCHEMA_DESIGN.md
    |-- LEGACY_STATE.md
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

### Run all the tests

```bash
python -m pytest framework/tests/ -v
```

---

## Proof, Not Just Claims

| What I claim                   | How I proved it                                                      |
| ------------------------------ | -------------------------------------------------------------------- |
| No duplicate rows              | Automated test checks the exact row count for every source           |
| Revisions get caught, not lost | Every load checks old values against new ones before saving          |
| Row counts are correct         | Each source has a test with a known, correct number to check against |
| Data is real, not made up      | Every file was checked by hand first. See docs/LEGACY_STATE.md       |

---

## What's Left To Do

- Add the rest of the Insolvency Service data (Northern Ireland, and a few more breakdowns)
- Add the rest of the ONS data (six more sheets)
- Set up automated testing on every code push
- Add proper scheduling with Airflow
- Build the final Gold layer using Spark and Delta Lake, with a real speed comparison
- Connect to Azure Databricks
- Build a Power BI dashboard on top of the finished data

---

## Author

**Ose Omokhua**
MSc Data Science, BSc Physics
London, UK

Open to Data Engineer and Data Scientist roles (UK and Remote)

[![GitHub](https://img.shields.io/badge/GitHub-insightful--algorithms-181717?style=flat&logo=github&logoColor=white)](https://github.com/insightful-algorithms)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/omokhua-ose)
