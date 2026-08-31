# Databricks notebook source
fsa_path = "/Volumes/pipeline_consolidation_databricks/bronze/raw_files/fsa"
files = dbutils.fs.ls(fsa_path)
for f in files:
    print(f.name, f.size)

# COMMAND ----------

df = spark.read.csv(
    "/Volumes/pipeline_consolidation_databricks/bronze/raw_files/fsa/20241213Rolling12MnthsofDebtorDaysInformationfortheMeatIndustryDebt.csv",
    header=True,
)
df.show()
print(f"Row count: {df.count()}")from pyspark.sql.functions import lit as spark_lit

# COMMAND ----------

from pyspark.sql.functions import lit as spark_lit

# Read the three real uploaded sources
fsa_df = spark.read.csv(
    "/Volumes/pipeline_consolidation_databricks/bronze/raw_files/fsa/20241213Rolling12MnthsofDebtorDaysInformationfortheMeatIndustryDebt.csv",
    header=True,
).select("InvoiceMonth", "MeatIndustry") \
 .withColumnRenamed("InvoiceMonth", "period") \
 .withColumnRenamed("MeatIndustry", "value") \
 .withColumn("source_publisher", spark_lit("FSA")) \
 .withColumn("indicator_code", spark_lit("MEAT_INDUSTRY_DEBTOR_DAYS"))

fsa_df.show()
print(f"FSA rows: {fsa_df.count()}")

# COMMAND ----------

(
    fsa_df.write
    .format("delta")
    .mode("overwrite")
    .saveAsTable("pipeline_consolidation_databricks.bronze.fact_debt_indicators_demo")
)

print("Written as a real Delta table.")

# COMMAND ----------

result = spark.sql("SELECT * FROM pipeline_consolidation_databricks.bronze.fact_debt_indicators_demo")
result.show()
print(f"Delta table row count: {result.count()}")

# COMMAND ----------

insolvency_df = spark.read.csv(
    "/Volumes/pipeline_consolidation_databricks/bronze/raw_files/insolvency_service/Long-Run_Series_in_CSV_Format_-_Individual_Insolvency_Statistics_July_2026.csv",
    header=True,
).select("period", "EW_total_individuals_NSA") \
 .withColumnRenamed("period", "period_raw") \
 .withColumnRenamed("EW_total_individuals_NSA", "value") \
 .withColumn("source_publisher", spark_lit("INSOLVENCY_SERVICE")) \
 .withColumn("indicator_code", spark_lit("EW_TOTAL_INDIVIDUALS_NSA")) \
 .filter("value IS NOT NULL AND value != '' AND value NOT IN ('[x]', '[z]')")

ofgem_df = spark.read.csv(
    "/Volumes/pipeline_consolidation_databricks/bronze/raw_files/ofgem/total-financial-value-of.csv",
    header=True,
).select("Category", "`Total debt Elec & Gas (£bn)`") \
 .withColumnRenamed("Category", "period_raw") \
 .withColumnRenamed("Total debt Elec & Gas (£bn)", "value") \
 .withColumn("source_publisher", spark_lit("OFGEM")) \
 .withColumn("indicator_code", spark_lit("TOTAL_DEBT_ELEC_GAS"))

print("Insolvency Service:", insolvency_df.count())
print("Ofgem:", ofgem_df.count())

# COMMAND ----------

fsa_silver = fsa_df.withColumnRenamed("period", "period_raw")

silver_all = fsa_silver.select("period_raw", "value", "source_publisher", "indicator_code") \
    .unionByName(insolvency_df.select("period_raw", "value", "source_publisher", "indicator_code")) \
    .unionByName(ofgem_df.select("period_raw", "value", "source_publisher", "indicator_code"))

silver_all.write.format("delta").mode("overwrite").saveAsTable(
    "pipeline_consolidation_databricks.bronze.silver_demo"
)
print(f"Combined Silver rows: {silver_all.count()}")

# COMMAND ----------

publisher_history = spark.createDataFrame([
    ("FSA_1900-01-01", "FSA", "FSA_DEBTOR_DAYS", "1900-01-01", "9999-12-31", True),
    ("INSOLVENCY_SERVICE_1900-01-01", "INSOLVENCY_SERVICE", "LONG_RUN_SERIES", "1900-01-01", "9999-12-31", True),
    ("OFGEM_1900-01-01", "OFGEM", "DEBT_ARREARS_INDICATORS", "1900-01-01", "9999-12-31", True),
    ("ONS_1900-01-01", "ONS", "RFTM18", "1900-01-01", "2025-05-31", False),
    ("ONS_2025-06-01", "ONS", "RFTM17", "2025-06-01", "9999-12-31", True),
], ["source_publisher_key", "source_publisher", "reference_code", "valid_from", "valid_to", "is_current"])

publisher_history.write.format("delta").mode("overwrite").saveAsTable(
    "pipeline_consolidation_databricks.bronze.dim_source_publisher"
)
print(f"dim_source_publisher rows: {publisher_history.count()}")

# COMMAND ----------

from pyspark.sql.functions import col as spark_col

dim_indicator_type = silver_all.select("indicator_code").distinct() \
    .withColumnRenamed("indicator_code", "indicator_type_key") \
    .withColumn("indicator_code", spark_col("indicator_type_key"))

dim_indicator_type.write.format("delta").mode("overwrite").saveAsTable(
    "pipeline_consolidation_databricks.bronze.dim_indicator_type"
)
print(f"dim_indicator_type rows: {dim_indicator_type.count()}")

# COMMAND ----------

fact = silver_all.join(
    publisher_history,
    on="source_publisher",
    how="left",
).select(
    "source_publisher_key",
    "indicator_code",
    "period_raw",
    "value",
)

fact.write.format("delta").mode("overwrite").saveAsTable(
    "pipeline_consolidation_databricks.bronze.fact_debt_indicators"
)
print(f"fact_debt_indicators rows: {fact.count()}")
fact.show()