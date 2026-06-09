# Databricks notebook source
# MAGIC %md
# MAGIC # 【Extra課題】system テーブルでコストを分析する
# MAGIC
# MAGIC Databricks の利用状況・コストは **`system.billing`** スキーマのテーブルで確認できます。
# MAGIC 「誰が・何に・どれだけ使ったか」を SQL で可視化してみましょう。
# MAGIC
# MAGIC > ℹ️ このノートブックは **持ち帰りの任意課題** です。実行には `system` スキーマ（`system.billing`）への
# MAGIC > SELECT 権限が必要です。権限がない場合は管理者に有効化を依頼してください。
# MAGIC
# MAGIC | テーブル | 内容 |
# MAGIC |---|---|
# MAGIC | `system.billing.usage` | 利用量（DBU）の明細。日付・SKU・ジョブ/ウェアハウス・実行者など |
# MAGIC | `system.billing.list_prices` | SKU ごとの単価（リスト価格） |

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. 直近30日の DBU 消費推移

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT usage_date, ROUND(SUM(usage_quantity), 2) AS dbus
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= current_date() - INTERVAL 30 DAYS
# MAGIC GROUP BY usage_date
# MAGIC ORDER BY usage_date

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. SKU（製品）別の DBU 消費
# MAGIC
# MAGIC サーバレス、ジョブ、SQL Warehouse など、どの種類のコンピュートで使っているか。

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT sku_name, ROUND(SUM(usage_quantity), 2) AS dbus
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= current_date() - INTERVAL 30 DAYS
# MAGIC GROUP BY sku_name
# MAGIC ORDER BY dbus DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. コストを試算する（単価テーブルと結合）
# MAGIC
# MAGIC `usage`（DBU量）に `list_prices`（単価）を掛けて、推定コストを出します。

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   u.sku_name,
# MAGIC   ROUND(SUM(u.usage_quantity), 2) AS dbus,
# MAGIC   ROUND(SUM(u.usage_quantity * lp.pricing.effective_list.default), 2) AS estimated_cost,
# MAGIC   MAX(lp.currency_code) AS currency
# MAGIC FROM system.billing.usage u
# MAGIC JOIN system.billing.list_prices lp
# MAGIC   ON u.sku_name = lp.sku_name
# MAGIC  AND u.usage_end_time >= lp.price_start_time
# MAGIC  AND (u.usage_end_time < lp.price_end_time OR lp.price_end_time IS NULL)
# MAGIC WHERE u.usage_date >= current_date() - INTERVAL 30 DAYS
# MAGIC GROUP BY u.sku_name
# MAGIC ORDER BY estimated_cost DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. 自分の利用分を見る
# MAGIC
# MAGIC `identity_metadata.run_as` で実行者を絞り、自分が動かしたジョブ等の消費を確認します。

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT usage_date,
# MAGIC        usage_metadata.job_id        AS job_id,
# MAGIC        usage_metadata.warehouse_id  AS warehouse_id,
# MAGIC        ROUND(SUM(usage_quantity), 2) AS dbus
# MAGIC FROM system.billing.usage
# MAGIC WHERE usage_date >= current_date() - INTERVAL 30 DAYS
# MAGIC   AND identity_metadata.run_as = current_user()
# MAGIC GROUP BY ALL
# MAGIC ORDER BY usage_date DESC, dbus DESC
# MAGIC LIMIT 50

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Genie Code / Genie Space で聞いてみる
# MAGIC
# MAGIC コスト分析も自然言語で。例:
# MAGIC - 「直近7日で最もDBUを消費したSKUは？」
# MAGIC - 「ジョブ別の推定コストを高い順に」
# MAGIC
# MAGIC > ガバナンスの観点でも、`system` スキーマには監査ログ（`system.access.audit`）やテーブル系譜
# MAGIC > （`system.access.table_lineage`）など、運用に役立つテーブルが揃っています。

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC - `system.billing.usage` × `system.billing.list_prices` でコストを可視化できる
# MAGIC - 「誰が・何に・いくら」を SQL や Genie で把握 → コスト管理・ガバナンスの第一歩
# MAGIC
# MAGIC これでハンズオンの全コンテンツは終了です。お疲れさまでした！
