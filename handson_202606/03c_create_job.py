# Databricks notebook source
# MAGIC %md
# MAGIC # Lakeflow Job を手動で作成する
# MAGIC
# MAGIC `03a_silver` / `03b_gold` の2つのノートブックを、
# MAGIC **依存関係を持つ1つのジョブ（パイプライン）**として Lakeflow Jobs（ワークフロー）で組み立てます。
# MAGIC
# MAGIC ```
# MAGIC [01_setup で投入済み] → [03a_silver] → [03b_gold]
# MAGIC      bronze_*            Bronze→Silver   Silver→Gold
# MAGIC ```
# MAGIC
# MAGIC > Bronze は `01_setup` で投入済みなので、パイプラインは **Silver → Gold の2タスク**です。
# MAGIC > 自動生成スクリプトは使わず、**自分の手でUIから組む**ことで、ジョブ・タスク・依存関係の仕組みを理解します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## はじめに：実行はこの Job 作成から行います
# MAGIC
# MAGIC `03a_silver` / `03b_gold` は**コードを読んで理解するだけ**で、手動実行はしていません。
# MAGIC ここで Lakeflow Job を組み立て、**Job を実行したときに初めて Silver → Gold が走ります**。
# MAGIC
# MAGIC > 💡 これが「パイプラインを実行する」ということ。各ノートブックを個別に手で回すのではなく、
# MAGIC > ジョブとしてまとめて・順番に・依存関係つきで実行します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: ジョブを新規作成し、Task 1（Silver）を追加
# MAGIC
# MAGIC 1. 左サイドバー → **ジョブとパイプライン（ワークフロー）** → **「作成」→「ジョブ」**
# MAGIC 2. 画面上部のジョブ名を `handson_pipeline_<名前>` に変更
# MAGIC 3. 最初のタスクを設定：
# MAGIC    - **タスク名**: `silver`
# MAGIC    - **種類**: ノートブック
# MAGIC    - **パス**: `03a_silver` を選択
# MAGIC    - **コンピュート**: サーバレス
# MAGIC 4. **「タスクを作成」** をクリック

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Task 2（Gold）を追加し、Silver に依存させる
# MAGIC
# MAGIC 1. DAG 画面で **「＋ タスクを追加」**
# MAGIC 2. 設定：
# MAGIC    - **タスク名**: `gold`
# MAGIC    - **種類**: ノートブック / **パス**: `03b_gold`
# MAGIC    - **依存先（Depends on）**: `silver` を選択 ← これで silver の後に実行される
# MAGIC    - **コンピュート**: サーバレス
# MAGIC 3. 作成
# MAGIC
# MAGIC これで `silver → gold` の2タスクが線でつながった DAG ができます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: 実行して観察する
# MAGIC
# MAGIC 1. 右上の **「今すぐ実行」** をクリック
# MAGIC 2. 画面上部のタブを **「タスク（Tasks）」から「実行（Runs）」に切り替える** → 実行中の run が一覧に表示される
# MAGIC 3. その run をクリックすると DAG が開き、各タスクが順番に **実行中 → 成功** と色が変わる様子をリアルタイムで確認できる
# MAGIC 4. タスクをクリックすると、そのノートブックの実行結果・ログが見られる
# MAGIC 5. 2タスクとも緑（成功）になれば完了 🎉
# MAGIC
# MAGIC > 💡 依存関係があるので、`silver` が失敗すると `gold` は実行されません。
# MAGIC > これが「パイプライン」。1か所直せば全体を再実行できます。

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: 結果を確認
# MAGIC
# MAGIC カタログエクスプローラで、自分のスキーマに次のテーブルができていることを確認しましょう。
# MAGIC
# MAGIC - `bronze_*`（4テーブル / 01_setup で作成済み）
# MAGIC - `silver_*`（4テーブル / Silver タスクで作成）
# MAGIC - `gold_monthly_engagement` / `gold_member_segment` / `gold_paywall_conversion`（Gold タスクで作成）

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

# MAGIC %sql
# MAGIC SHOW TABLES

# COMMAND ----------

# MAGIC %md
# MAGIC ## このあと（口頭で紹介）：Unity Catalog の便利機能
# MAGIC
# MAGIC パイプラインが完成したので、Unity Catalog の機能が映えます。講師が画面で紹介します。
# MAGIC
# MAGIC | 機能 | 何が分かる |
# MAGIC |---|---|
# MAGIC | **リネージ（Lineage）** | `bronze → silver → gold` のデータの流れが図で見える。どのテーブルがどこから来たか追跡できる |
# MAGIC | **Insights** | テーブルがどのクエリ・誰によく使われているか |
# MAGIC | **Quality / プロファイル** | カラムの分布・NULL率・統計など、データ品質の概観 |
# MAGIC
# MAGIC **次のステップ:** `04_analysis` で、いよいよ自分でデータ分析（churn 分析）に挑戦します。
