# Databricks notebook source
# MAGIC %md
# MAGIC # Task 1: Silver — データ変換・クレンジング
# MAGIC
# MAGIC Bronze をクレンジングし、分析に使いやすい **Silver テーブル**に変換します。
# MAGIC
# MAGIC ```
# MAGIC メダリオンアーキテクチャ:
# MAGIC   Bronze → [Silver] → Gold
# MAGIC            ^^^ 今ここ（Bronze は 01_setup で投入済み）
# MAGIC ```
# MAGIC
# MAGIC > 📖 **このノートブックは中身を読んで理解するだけ。ここでは実行しません。**
# MAGIC > 実際の実行は、次の `03c_create_job` で Lakeflow Job を作成・実行したときに行われます
# MAGIC > （Job が `03a_silver` → `03b_gold` の順に走らせます）。
# MAGIC
# MAGIC **主な変換**
# MAGIC - 日付/日時の型変換（文字列 → date / timestamp）
# MAGIC - 年齢層（`age_group`）・年月（`ym`）カラムの付与
# MAGIC - `reading_logs` に `articles` を JOIN して `category` / `is_premium` を付与
# MAGIC - `subscriptions` に契約日数（`tenure_days`）・解約年月（`churn_ym`）を付与

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import DateType, TimestampType

print(f"対象: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## silver_members — 年齢層を付与

# COMMAND ----------

members = (
    spark.table(f"{catalog}.{schema}.bronze_members")
    .withColumn("registration_date", F.expr("try_cast(registration_date AS DATE)"))
    .withColumn("age_group",
        F.when(F.col("age") < 30, "20代以下")
         .when(F.col("age") < 40, "30代")
         .when(F.col("age") < 50, "40代")
         .when(F.col("age") < 60, "50代")
         .otherwise("60代以上"))
)
(members.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.silver_members"))
print(f"silver_members: {members.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## silver_articles — 日付型変換

# COMMAND ----------

articles = (
    spark.table(f"{catalog}.{schema}.bronze_articles")
    .withColumn("publish_date", F.expr("try_cast(publish_date AS DATE)"))
)
(articles.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.silver_articles"))
print(f"silver_articles: {articles.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## silver_reading_logs — 日時変換 + 年月付与 + 記事カテゴリの結合
# MAGIC
# MAGIC 行動ログに記事マスタを JOIN し、`category` と `is_premium` を持たせます（後続の分析が JOIN なしで書けるようになる）。

# COMMAND ----------

logs = (
    spark.table(f"{catalog}.{schema}.bronze_reading_logs")
    .withColumn("event_time", F.expr("try_cast(event_time AS TIMESTAMP)"))
    .withColumn("event_date", F.to_date("event_time"))
    .withColumn("ym", F.date_format("event_time", "yyyy-MM"))
)
art = spark.table(f"{catalog}.{schema}.silver_articles").select("article_id", "category", "is_premium")

logs = logs.join(art, on="article_id", how="left")

(logs.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.silver_reading_logs"))
print(f"silver_reading_logs: {logs.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## silver_subscriptions — 日付変換 + 契約日数 + 解約年月
# MAGIC
# MAGIC `end_date` が空（継続中）の場合は NULL になります。解約済みのレコードには解約年月（`churn_ym`）を付与します。

# COMMAND ----------

subs = (
    spark.table(f"{catalog}.{schema}.bronze_subscriptions")
    .withColumn("start_date", F.expr("try_cast(start_date AS DATE)"))
    .withColumn("end_date", F.expr("try_cast(end_date AS DATE)"))   # 空文字 "" や不正値は NULL になる（try_cast なので例外にならない）
    .withColumn("churn_ym",
        F.when(F.col("status") == "churned", F.date_format("end_date", "yyyy-MM")))
    .withColumn("tenure_days",
        F.when(F.col("end_date").isNotNull(), F.datediff("end_date", "start_date")))
)
(subs.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.silver_subscriptions"))
print(f"silver_subscriptions: {subs.count():,} rows")

# COMMAND ----------

print("\nTask 2 完了: 4つの Silver テーブルを作成しました")
print("  bronze_*（生データ）→ silver_*（型変換・カラム付与・結合済み）")
