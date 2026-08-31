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