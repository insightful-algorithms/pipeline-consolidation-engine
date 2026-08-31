"""
Exports the full local Gold layer (all 12 sources) as flat CSVs, ready
for Power BI. The fact export pre-joins publisher and indicator names
directly, so Power BI needs no relationship modelling -- same
principle as the earlier Databricks flat export, applied here to the
complete local Gold layer instead of the 3-source Databricks subset.
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect("warehouse/dev.db")

fact = pd.read_sql("""
    SELECT
        f.date_key,
        f.indicator_value,
        f.dim_supplier,
        p.source_publisher,
        p.reference_code,
        i.indicator_code,
        i.indicator_name,
        i.unit
    FROM fact_debt_indicators f
    LEFT JOIN dim_source_publisher p ON f.source_publisher_key = p.source_publisher_key
    LEFT JOIN dim_indicator_type i ON f.indicator_type_key = i.indicator_type_key
""", conn)

publishers = pd.read_sql("SELECT * FROM dim_source_publisher", conn)
dates = pd.read_sql("SELECT * FROM dim_date", conn)

conn.close()

fact.to_csv("power-bi-data/fact_full.csv", index=False)
publishers.to_csv("power-bi-data/dim_source_publisher_full.csv", index=False)
dates.to_csv("power-bi-data/dim_date_full.csv", index=False)

print(f"Fact rows: {len(fact)}")
print(f"Publisher rows: {len(publishers)}")
print(f"Date rows: {len(dates)}")