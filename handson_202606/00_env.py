# Databricks notebook source
# MAGIC %md
# MAGIC # 環境設定
# MAGIC
# MAGIC **以下の `schema` を自分の名前に変更してください。**
# MAGIC
# MAGIC このノートブックは他のノートブックから `%run ./00_env` で呼び出されます。
# MAGIC ここを1回変更すれば、全てのノートブックに反映されます。
# MAGIC
# MAGIC | 設定 | 説明 |
# MAGIC |---|---|
# MAGIC | `catalog` | 代表者が作成した**共有カタログ**。変更不要 |
# MAGIC | `schema`  | **自分専用のスキーマ**。他の人と重複しない名前にしてください（例: `schema_yamada`） |

# COMMAND ----------

catalog = "handson_202606"   # ← 変更不要（共有カタログ）
schema  = ""                  # ← 自分のスキーマ名に変更してください（例: schema_yamada）

assert catalog != "", "カタログ名を設定してください"
assert schema  != "", "スキーマ名を設定してください（00_env を開いて schema を変更）"

# 自分のスキーマを作成して切り替える（既にあればそのまま使う）
spark.sql(f"USE CATALOG {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")
spark.sql(f"USE SCHEMA {schema}")

print(f"カタログ: {catalog}")
print(f"スキーマ: {schema}")
