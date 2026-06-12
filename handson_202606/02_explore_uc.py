# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog でデータを探索する
# MAGIC
# MAGIC `01_setup` で 4つの **Bronze テーブル**を Unity Catalog に登録しました。
# MAGIC パイプラインを作る前に、まず **Unity Catalog** でデータの全体像をつかみましょう。
# MAGIC
# MAGIC | テーブル | 主なカラム |
# MAGIC |---|---|
# MAGIC | `bronze_members` | member_id, age, gender, prefecture, occupation, **plan_type**(free/paid/premium) |
# MAGIC | `bronze_articles` | article_id, title, **category**, publish_date, **is_premium** |
# MAGIC | `bronze_reading_logs` | log_id, member_id, article_id, **event_type**, event_time, device |
# MAGIC | `bronze_subscriptions` | subscription_id, member_id, plan_type, start_date, **end_date**, **status** |

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: カタログエクスプローラでテーブルを眺める
# MAGIC
# MAGIC 左サイドバーの **「カタログ」** をクリックし、`00_env` で設定した共有カタログ → 自分のスキーマ → テーブル一覧を開いてください。
# MAGIC
# MAGIC **`bronze_reading_logs`** をクリックして、以下のタブを確認しましょう。
# MAGIC
# MAGIC | タブ | 確認ポイント |
# MAGIC |---|---|
# MAGIC | **概要 / スキーマ** | どんなカラムがある？ `event_type` にはどんな種類がありそう？ |
# MAGIC | **サンプルデータ** | 実データをプレビュー。`event_type` の値（read_complete / paywall_hit / subscribe …）を眺める |
# MAGIC | **詳細** | 行数・サイズ。データの規模感をつかむ |
# MAGIC
# MAGIC 同じように `bronze_members` / `bronze_articles` / `bronze_subscriptions` も覗いてみてください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: ⭐ AIに「テーブルの説明文」を生成してもらう
# MAGIC
# MAGIC Unity Catalog には、テーブルやカラムの**説明（コメント）をAIが提案してくれる機能**があります。
# MAGIC 説明を付けておくと、人にもAI（後で使う Genie）にも分かりやすいデータになります。
# MAGIC
# MAGIC ### やってみよう
# MAGIC 1. カタログエクスプローラで **`bronze_reading_logs`** テーブルを開く
# MAGIC 2. 概要（Overview）の **コメント欄**、またはカラム一覧の説明欄にある **✨（AI生成 / AI suggest）** をクリック
# MAGIC 3. AIが生成した説明文の提案が表示される → 内容を確認
# MAGIC 4. 問題なければ **「承認（Accept）」** で保存。おかしければ手で直してもOK
# MAGIC 5. カラムの説明も同様に、提案を確認して **まとめて承認** できます
# MAGIC
# MAGIC > 💡 AIはカラム名やサンプルデータから意味を推測します。`event_type` や `is_premium` にどんな説明が付くか見てみましょう。
# MAGIC > この説明（メタデータ）が、後半の **Genie Space の回答精度** に効いてきます。
# MAGIC
# MAGIC 余裕があれば `bronze_members` / `bronze_subscriptions` でも AI 説明文を試してください。

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: 【クイズ】テーブルのつながりを考える
# MAGIC
# MAGIC テーブル同士の関係を図にすると、こうなっています。
# MAGIC
# MAGIC ```
# MAGIC bronze_members (member_id)
# MAGIC   ├── 1:N → bronze_reading_logs (member_id) ──N:1── bronze_articles (article_id)
# MAGIC   └── 1:N → bronze_subscriptions (member_id)
# MAGIC ```
# MAGIC
# MAGIC ### Q1. 行動ログ `bronze_reading_logs` は、どのカラムで他のテーブルと JOIN できる？
# MAGIC
# MAGIC まず自分で考えてみましょう。考えたら下の非表示のセルに回答があります

# COMMAND ----------

"""
bronze_members とは member_id で JOIN（＝誰が読んだか）
bronze_articles とは article_id で JOIN（＝どの記事を読んだか）
bronze_reading_logs は両方のIDを持つ「中間テーブル」なので、会員属性と記事属性の両方を結びつけられます。
"""

# COMMAND ----------

# MAGIC %md
# MAGIC ### Q2. 「会員ごとの読了数」を出すには、どのテーブルをどう組み合わせる？
# MAGIC
# MAGIC 「読了」は `event_type = 'read_complete'` です。
# MAGIC まず下のセルで自分で書いてみましょう（会員名も一緒に出すには？）。書けたら、その下の「答えを見る」で答え合わせ。

# COMMAND ----------

#Q2: 会員ごとの読了数を出してみよう
# ヒント: event_type = 'read_complete' に絞って member_id で集計（COUNT + GROUP BY）
# 下の SELECT を書き換えてみてください（テーブルは {catalog}.{schema}. で完全修飾）

display(spark.sql(f"""
SELECT member_id
FROM {catalog}.{schema}.bronze_reading_logs
LIMIT 10
"""))


# COMMAND ----------

#member_id 単位なら bronze_reading_logs だけで集計できます。

display(spark.sql(f"""
    SELECT member_id, COUNT(*) AS reads_completed
    FROM {catalog}.{schema}.bronze_reading_logs
    WHERE event_type = 'read_complete'
    GROUP BY member_id
    ORDER BY reads_completed DESC
"""))
#会員名やプランも一緒に出したいなら、bronze_members を member_id で JOIN します。

display(spark.sql(f"""
    SELECT m.member_id, m.name, m.plan_type,
           COUNT(*) AS reads_completed
    FROM {catalog}.{schema}.bronze_reading_logs r
    JOIN {catalog}.{schema}.bronze_members m ON r.member_id = m.member_id
    WHERE r.event_type = 'read_complete'
    GROUP BY m.member_id, m.name, m.plan_type
    ORDER BY reads_completed DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: 簡単な集計でデータを感じる
# MAGIC
# MAGIC ここからはノートブックで軽く集計してみます。
# MAGIC
# MAGIC > 💡 受講者ごとにスキーマ名が違うため、テーブルは `カタログ.スキーマ.テーブル` と**完全修飾**で指定します。
# MAGIC > `spark.sql()` に `00_env` で設定した `catalog` / `schema` 変数を埋め込み、`display()` で表示します
# MAGIC > （結果テーブルの **＋ > 可視化** でグラフも作れます）。

# COMMAND ----------

# MAGIC %md
# MAGIC ### プラン別の会員数

# COMMAND ----------

display(spark.sql(f"""
    SELECT plan_type, COUNT(*) AS members
    FROM {catalog}.{schema}.bronze_members
    GROUP BY plan_type
    ORDER BY members DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### イベント種別の内訳
# MAGIC
# MAGIC `bronze_reading_logs` にどんな行動が記録されているか見てみましょう。`paywall_hit`（ペイウォール接触）や `subscribe`（課金）に注目。

# COMMAND ----------

display(spark.sql(f"""
    SELECT event_type, COUNT(*) AS cnt
    FROM {catalog}.{schema}.bronze_reading_logs
    GROUP BY event_type
    ORDER BY cnt DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 月別の記事閲覧数（読了 vs 離脱）
# MAGIC
# MAGIC 💡 結果テーブルの右にある **＋ > 可視化** で折れ線グラフにしてみましょう。何か気づきはありますか？
# MAGIC （※ Bronze の `event_time` は文字列なので、`to_timestamp` で日時に直してから年月を取り出しています）

# COMMAND ----------

display(spark.sql(f"""
    SELECT date_format(to_timestamp(event_time), 'yyyy-MM') AS ym,
           COUNT(*) AS article_views,
           SUM(CASE WHEN event_type = 'read_complete' THEN 1 ELSE 0 END) AS reads_completed
    FROM {catalog}.{schema}.bronze_reading_logs
    WHERE event_type IN ('read_start', 'read_complete')
    GROUP BY 1
    ORDER BY 1
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Genie Code（セル内AIアシスタント）を使ってみる
# MAGIC
# MAGIC 本セルの下にカーソルを合わせると表示される **Genie Code** のボタンをクリックします。そこでは自然言語でクエリを作成できます。
# MAGIC
# MAGIC **プロンプト例**：「テクノロジーカテゴリの月別の読了率を計算して」
# MAGIC
# MAGIC > ※ いまは `bronze_reading_logs` に `category` がありません（記事マスタ側が持っている）。
# MAGIC > 次の Lakeflow パイプライン（Silver）で記事カテゴリを結合します。
# MAGIC > 「カテゴリ別に見たい」という気持ちが、これから作るパイプラインの動機になります。

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC - Unity Catalog でテーブルの中身・スキーマ・サンプルを確認した
# MAGIC - **AIに説明文を生成**させてメタデータを整えた
# MAGIC - テーブルのリレーションと、分析の切り口（プラン・カテゴリ・イベント種別）を把握した
# MAGIC
# MAGIC **次のステップ:** `03a_silver` → `03b_gold` で**コードを確認**し、`03c_create_job` で Lakeflow Job を組んで実行します。