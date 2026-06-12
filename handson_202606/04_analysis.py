# Databricks notebook source
# MAGIC %md
# MAGIC # 自分で分析してみよう — 解約（churn）と会員行動
# MAGIC
# MAGIC パイプラインで `silver_*` / `gold_*` テーブルが揃いました。
# MAGIC ここからは **自分でクエリを書いて** ビジネス上の問いに答えてみましょう。
# MAGIC
# MAGIC > ⚠️ このセクションは少し歯ごたえがあります。**手が止まってもOK**。
# MAGIC > 詰まったら **Genie Code（✨）** に書かせても構いません。
# MAGIC > …そして次の `05_genie_space` では、これらの問いが **どれだけ楽になるか** を体験します。
# MAGIC
# MAGIC **使えるテーブル（一部）:**
# MAGIC
# MAGIC | テーブル | 主なカラム |
# MAGIC |---|---|
# MAGIC | `silver_subscriptions` | member_id, plan_type, start_date, **end_date**, **status**, **churn_ym**, tenure_days |
# MAGIC | `silver_members` | member_id, age_group, plan_type, prefecture |
# MAGIC | `silver_reading_logs` | member_id, event_type, event_date, ym, category, is_premium |
# MAGIC | `gold_member_segment` | member_id, plan_type, age_group, total_events, last_event_date, activity_segment |

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

# MAGIC %md
# MAGIC ## はじめに: どんなテーブルができたか確認しよう
# MAGIC
# MAGIC 問題に入る前に、パイプラインで作られたデータを確認します。
# MAGIC
# MAGIC 左サイドバーの **カタログ** → `00_env` で設定した共有カタログ → 自分のスキーマ を開くと、
# MAGIC `bronze_* / silver_* / gold_*` のテーブルが並んでいるはずです。
# MAGIC ノートブックからも一覧できます（下のセルを実行）。

# COMMAND ----------

# 自分のスキーマにあるテーブル一覧
display(spark.sql(f"SHOW TABLES IN {catalog}.{schema}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 今回の分析で使う主なテーブルの中身を、先頭数行のぞいてみる
# MAGIC
# MAGIC どんなカラムがあって、どんな値が入っているかを掴んでから問題に進みましょう。

# COMMAND ----------

# silver_subscriptions: 購読履歴（解約分析の主役）。status / end_date / churn_ym に注目
display(spark.sql(f"SELECT * FROM {catalog}.{schema}.silver_subscriptions LIMIT 5"))

# COMMAND ----------

# silver_members: 会員属性（age_group / plan_type）
display(spark.sql(f"SELECT * FROM {catalog}.{schema}.silver_members LIMIT 5"))

# COMMAND ----------

# gold_member_segment: 会員ごとの行動サマリー（last_event_date / activity_segment）
display(spark.sql(f"SELECT * FROM {catalog}.{schema}.gold_member_segment LIMIT 5"))

# COMMAND ----------

# gold_paywall_conversion: 年月×年代別のペイウォール接触→転換（問4で使う）
display(spark.sql(f"SELECT * FROM {catalog}.{schema}.gold_paywall_conversion LIMIT 5"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 問1: 解約はいつ増えた？（月別の解約件数の推移）
# MAGIC
# MAGIC `silver_subscriptions` の `status = 'churned'` を `churn_ym`（解約年月）で集計してみましょう。
# MAGIC 折れ線グラフにすると傾向が見やすいです。
# MAGIC
# MAGIC 💡 ヒント: `WHERE status = 'churned'` → `GROUP BY churn_ym`

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ここに書いてみましょう

# COMMAND ----------

# MAGIC %md
# MAGIC ## 問2: 解約が増えたのはどの年代？
# MAGIC
# MAGIC 解約レコードに会員属性を結びつけて、**年代別**の解約傾向を見てみましょう。
# MAGIC
# MAGIC 💡 ヒント: `silver_subscriptions`(churned) と `silver_members` を `member_id` で JOIN し、`age_group` 別・`churn_ym` 別に集計。
# MAGIC 2025年後半に注目。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ここに書いてみましょう

# COMMAND ----------

# MAGIC %md
# MAGIC ## 問3:（難）サイレント離脱の予兆 — 「まだ解約していないが、最近読んでいない有料会員」
# MAGIC
# MAGIC > 🤖 **問3以降は、画面右上の Genie Code も頼っていきましょう！**
# MAGIC > 「この問題3を解いて」と Genie Code に指示して解いてみても OK！
# MAGIC
# MAGIC 解約に至っていなくても、**しばらく記事を読んでいない有料会員**は離脱リスクが高いはず。
# MAGIC 「有料 / プレミアム会員のうち、直近90日間まったく読んでいない人」を抽出してみましょう。
# MAGIC
# MAGIC 💡 ヒント:
# MAGIC - 会員ごとの最終アクセス日 = `silver_reading_logs` を `member_id` で集計して `MAX(event_date)`
# MAGIC - データ上の「現在」= ログ全体の最大日（`SELECT MAX(event_date) FROM silver_reading_logs`）
# MAGIC - そこから `datediff` で経過日数を計算し、`plan_type IN ('paid','premium')` かつ 90日超で絞る
# MAGIC - `gold_member_segment` の `last_event_date` を使うと少し楽になります

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ここに書いてみましょう（複数テーブル＋日付計算で少し大変です）

# COMMAND ----------

# MAGIC %md
# MAGIC ## 問4:（横断）ペイウォールに当たっているのに課金しない年代は？
# MAGIC
# MAGIC `gold_paywall_conversion` を使って、年代別の **転換率**（conversions / paywall_hits）を比べてみましょう。
# MAGIC 「接触は多いのに転換率が低い」年代が、課金導線の改善ターゲットです。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ここに書いてみましょう

# COMMAND ----------

# MAGIC %md
# MAGIC ## 振り返り
# MAGIC
# MAGIC - JOIN・日付計算・サブクエリ…と、ちょっとした分析でも書くことが多かったのではないでしょうか
# MAGIC - 「現在日からの経過日数」「年代別の比較」など、SQL に慣れていないと手が止まりがち
# MAGIC
# MAGIC **次の `05_genie_space` では、同じ問いを日本語で投げるだけで答えが返ってくる**様子を体験します。
