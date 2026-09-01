# Pipeline Consolidation Engine

[![Pipeline Consolidation CI](https://github.com/insightful-algorithms/pipeline-consolidation-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/insightful-algorithms/pipeline-consolidation-engine/actions/workflows/ci.yml)

A pipeline that pulls together UK government debt and financial hardship data from four different publishers, and puts it all into one clean, queryable format. Built end to end, from raw files to a working Power BI dashboard.

Built with Python, PyYAML, SQLite, Apache Airflow, Azure Databricks, and Power BI.

---

## The Problem

UK government debt data is published by four separate bodies. The Food Standards Agency, the Insolvency Service, Ofgem, and the Office for National Statistics. Each one publishes on its own schedule, in its own file format, with its own column names. There is no single place to see all of this data together.

Right now, if you wanted a full picture, you would have to visit four different websites, download four different file types, and piece it together by hand.

This project fixes that. It pulls real files from all four sources, checks them properly, loads them into one shared table, builds a proper dimensional model on top, and puts the result in front of a real dashboard. It also catches duplicate data automatically, and it catches when a publisher quietly revises an old figure.

---

## Why This Project Is Different

**Every file is real.** Nothing here is made up. About 155 files were checked by hand before deciding which were worth keeping. Every decision to keep or drop a file is backed by something I actually checked, not a guess.

**Revision detection actually works, and I proved it.** I found, by hand, a figure from the Insolvency Service that had quietly changed between two releases. Once the pipeline was built, it caught that exact same change on its own, plus hundreds more I had not found by hand, across three different sources.

**The design holds up across very different data.** Each new source I added broke an assumption the code had made for the source before it. Instead of patching around each problem, I changed the design so it could handle all of them properly. That includes a source shaped like one row per file, a source shaped like many small standalone indicators, and a source where one wide row had to be turned into many separate rows.

**I hit real infrastructure problems and solved them honestly.** Spark would not run locally on Windows due to a networking issue. Azure Databricks hit a VM quota limit. A SQL Warehouse hit the same limit again. Power BI Service could not upload a file because of a licensing gap. Every one of these is documented below, with the real fix, not hidden.

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

One shared table (SQLite)
   One row per publisher, indicator, place, and time period

        |
        v

Gold layer (real star schema)
   One fact table and three dimension tables, including one that
   tracks a real change in how ONS names its own reference tables

        |
        v

Azure Databricks (real Delta Lake tables)
   The same star schema, rebuilt on managed cloud Spark

        |
        v

Power BI (real dashboard)
   Charts and tables built on the finished Gold layer
```

---

## The Four Data Sources

| Source                | What it publishes                                                      | Files kept | The tricky part                                                                                               |
| --------------------- | ---------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| Food Standards Agency | Meat industry debtor days                                              | 4 of 18    | Mixed CSV and Excel files, overlapping date ranges                                                            |
| Insolvency Service    | Bankruptcies, DROs, IVAs, Northern Ireland, authorising body breakdown | 12 of 100+ | Old figures get quietly revised over time. One table had to be turned from a wide layout into individual rows |
| Ofgem                 | Energy debt and arrears                                                | 13 of 26   | Some files have no dates at all, just supplier names                                                          |
| ONS                   | Government deficit and debt, seven tables                              | 3 of 10    | One column mixes four different date formats. One table's own publisher renamed it partway through            |

---

## Key Decisions I Made

**Config files, not hardcoded scripts.** Adding a new data source means writing a config file, not new code. I proved this by adding several very different sources after the first one, without rewriting the core logic each time. The engine detects which shape a config is and picks the right loading strategy automatically.

**No duplicate data, ever.** Every row gets a unique ID based on its publisher, indicator, place, and date. Running the pipeline twice never creates duplicates. I proved this directly. The old, naive way of loading FSA data created 48 rows when there should only be 32. The new way loads exactly 32, every single time.

**The Insolvency Service config was generated, not typed by hand.** It has 30 different indicators, and I wrote a script that reads the publisher's own metadata file and builds the config from it automatically.

**Old figures that change are tracked, not overwritten.** Before saving a new value, the pipeline checks what is already there. If a figure changed, it logs the old value, the new value, and where each one came from.

**No SQL injection risk.** Every value going into the database is passed in separately from the SQL command itself. The database can never mistake a piece of data for an instruction.

**The Gold layer tracks a real change in a publisher's own naming.** ONS renamed one of its reference tables partway through the period this project covers, and dropped a table of its own official revisions at the same time. The publisher dimension in the Gold layer records both versions properly, with the exact dates each one was in use. This is real Slowly Changing Dimension Type 2 tracking, not a made up example.

**Orchestrated with Apache Airflow.** Every source loads through a scheduled, monitored task rather than being run by hand. The twelve sources are genuinely independent of each other, so they run in parallel rather than one after another.

**Spark and Delta Lake were built on Azure Databricks, not locally.** I tried to run PySpark and Delta Lake locally on Windows first. It failed on a networking issue between Spark's own internal processes, a known problem on that platform. Rather than give up on Spark entirely, I built and proved the exact same Gold layer design on Azure Databricks instead, which runs Spark properly with no networking issues. The local SQLite version and the cloud Delta Lake version share the same design.

**Power BI connects to the finished Gold layer.** The dashboard includes a chart of debt indicator volume by publisher, a time series of individual insolvencies going back to 2000, a scale summary, and a table showing the SCD Type 2 history for ONS directly. That last table is the clearest piece of evidence in the whole project. You can see ONS's two reference table versions sitting side by side, with the exact dates each one was valid.

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
|   |-- export_gold_for_powerbi.py  Exports the Gold layer for Power BI
|-- databricks/
|   |-- build_gold_databricks.py    Same star schema, built on Azure
|-- power-bi-data/
|   |-- debt-consolidation-dashboard.pbix
|-- warehouse/                  The database file, not stored in git
|-- framework/
|   |-- config/
|   |   |-- sources/             One config file per data source
|   |-- readers/                  Reads CSV and Excel files
|   |-- transformers/              Cleans and shapes the data
|   |-- loaders/                    Loads it into the database
|   |-- engine.py                    Runs the whole pipeline
|   |-- tests/                        Automated tests, one per source, plus
|                                      reusable diagnostic tools
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

### Export the Gold layer for Power BI

```bash
python gold/export_gold_for_powerbi.py
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

| What I claim                                 | How I proved it                                                                                        |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| No duplicate rows                            | Automated test checks the exact row count for every source                                             |
| Revisions get caught, not lost               | Every load checks old values against new ones before saving                                            |
| Row counts are correct                       | Each source has a test with a known, correct number to check against                                   |
| Data is real, not made up                    | Every file was checked by hand first. See docs/LEGACY_STATE.md                                         |
| Tests genuinely pass, not just on my machine | Every push runs the full test suite on a fresh GitHub hosted machine. See the CI badge above           |
| The Gold layer is correct                    | Row counts checked at every stage, joins verified with a dedicated diagnostic script                   |
| Delta Lake genuinely works on Azure          | Tables written and then read back independently in a fresh query, not just trusted                     |
| The dashboard uses real data                 | Every visual is built directly on the exported Gold layer, 10,407 real rows across all four publishers |

---

---

## Author

**Ose Omokhua**
MSc Data Science, BSc Physics
London, UK

Open to Data Engineer and Data Scientist roles (UK and Remote)

[![GitHub](https://img.shields.io/badge/GitHub-insightful--algorithms-181717?style=flat&logo=github&logoColor=white)](https://github.com/insightful-algorithms)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white)](https://linkedin.com/in/omokhua-ose)
