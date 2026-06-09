# Databricks notebook source
# MAGIC %md
# MAGIC # Task 2: Gold — マートテーブル作成
# MAGIC
# MAGIC Silver から、ビジネス分析・ダッシュボード・Genie 用の **Gold テーブル**（集計マート）を作成します。
# MAGIC
# MAGIC ```
# MAGIC メダリオンアーキテクチャ:
# MAGIC   Bronze → Silver → [Gold]
# MAGIC                      ^^^ 今ここ
# MAGIC ```
# MAGIC
# MAGIC > 📖 **このノートブックは中身を読んで理解するだけ。ここでは実行しません。**
# MAGIC > 実際の実行は、次の `03c_create_job` で Lakeflow Job を作成・実行したときに行われます。
# MAGIC
# MAGIC | テーブル | 内容 |
# MAGIC |---|---|
# MAGIC | `gold_monthly_engagement` | 月別×カテゴリ別の閲覧数・読了数・読了率・ユニーク読者数 |
# MAGIC | `gold_member_segment` | 会員ごとの行動サマリー（プラン × 利用頻度セグメント） |
# MAGIC | `gold_paywall_conversion` | 年月×年代別のペイウォール接触 → 課金転換 |
# MAGIC
# MAGIC > **解約（churn）の集計マートはあえて作りません。** 次の `04_analysis` で「自分で分析する題材」として残しています。

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

from pyspark.sql import functions as F

print(f"対象: {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_monthly_engagement — 月別×カテゴリ別エンゲージメント
# MAGIC
# MAGIC `article_views`（記事を開いた数）と `reads_completed`（読了数）から **読了率** を出します。
# MAGIC テクノロジーカテゴリの推移に注目してみてください。

# COMMAND ----------

logs = spark.table(f"{catalog}.{schema}.silver_reading_logs")

monthly = (
    logs.filter(F.col("event_type").isin("read_start", "read_complete"))
    .groupBy("ym", "category")
    .agg(
        F.count("*").alias("article_views"),
        F.sum(F.when(F.col("event_type") == "read_complete", 1).otherwise(0)).alias("reads_completed"),
        F.countDistinct("member_id").alias("unique_readers"),
    )
    .withColumn("completion_rate",
        F.round(F.col("reads_completed") / F.col("article_views") * 100, 1))
    .orderBy("ym", "category")
)
(monthly.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.gold_monthly_engagement"))
print(f"gold_monthly_engagement: {monthly.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_member_segment — 会員別 行動サマリー
# MAGIC
# MAGIC 会員ごとに行動を集計し、利用頻度で **ヘビー / 通常 / ライト / 休眠** に分類します。プラン・年代と掛け合わせて分析できます。

# COMMAND ----------

members = spark.table(f"{catalog}.{schema}.silver_members")

per_member = (
    logs.groupBy("member_id")
    .agg(
        F.count("*").alias("total_events"),
        F.sum(F.when(F.col("event_type") == "read_complete", 1).otherwise(0)).alias("reads_completed"),
        F.sum(F.when(F.col("event_type") == "paywall_hit", 1).otherwise(0)).alias("paywall_hits"),
        F.sum(F.when(F.col("event_type") == "subscribe", 1).otherwise(0)).alias("conversions"),
        F.max("event_date").alias("last_event_date"),
    )
)

segment = (
    members.join(per_member, on="member_id", how="left")
    .fillna(0, subset=["total_events", "reads_completed", "paywall_hits", "conversions"])
    .withColumn("activity_segment",
        F.when(F.col("total_events") >= 20, "ヘビーリーダー")
         .when(F.col("total_events") >= 8, "通常")
         .when(F.col("total_events") >= 2, "ライト")
         .otherwise("休眠"))
    .select("member_id", "plan_type", "age_group", "prefecture",
            "total_events", "reads_completed", "paywall_hits", "conversions",
            "last_event_date", "activity_segment")
)
(segment.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.gold_member_segment"))
print(f"gold_member_segment: {segment.count():,} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## gold_paywall_conversion — ペイウォール接触 → 課金転換
# MAGIC
# MAGIC 年月×年代別に、無料会員のペイウォール接触数と、そこからの課金転換数・転換率を集計します。
# MAGIC 「接触は多いのに転換しない年代」が見えるはずです。

# COMMAND ----------

logs_with_age = logs.join(members.select("member_id", "age_group"), on="member_id", how="left")

paywall = (
    logs_with_age.filter(F.col("event_type").isin("paywall_hit", "subscribe"))
    .groupBy("ym", "age_group")
    .agg(
        F.sum(F.when(F.col("event_type") == "paywall_hit", 1).otherwise(0)).alias("paywall_hits"),
        F.sum(F.when(F.col("event_type") == "subscribe", 1).otherwise(0)).alias("conversions"),
    )
    .withColumn("conversion_rate",
        F.round(F.col("conversions") / F.col("paywall_hits") * 100, 1))
    .orderBy("ym", "age_group")
)
(paywall.write.format("delta").mode("overwrite")
 .option("overwriteSchema", "true")
 .saveAsTable(f"{catalog}.{schema}.gold_paywall_conversion"))
print(f"gold_paywall_conversion: {paywall.count():,} rows")

# COMMAND ----------

print("\nTask 3 完了: 3つの Gold マートを作成しました")
