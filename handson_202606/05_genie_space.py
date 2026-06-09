# Databricks notebook source
# MAGIC %md
# MAGIC # Genie Space で分析する — さっきの問いが一瞬で
# MAGIC
# MAGIC `04_analysis` では SQL で手こずったかもしれません。
# MAGIC ここでは **Genie Space** に同じ問いを日本語で投げて、どれだけ楽になるかを体験します。
# MAGIC
# MAGIC ```
# MAGIC 流れ:
# MAGIC   1. テーブル・カラムにコメントを付ける（このノートブック）
# MAGIC   2. Genie Space を UI で作成
# MAGIC   3. まずメタデータだけで質問
# MAGIC   4. Instructions で社内用語を教えて精度アップ
# MAGIC ```

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: テーブル・カラムにコメントを付ける
# MAGIC
# MAGIC Genie はテーブル・カラムのコメントを読んでデータの意味を理解します。
# MAGIC `02` では生テーブルに AI でコメントを付けましたが、ここでは Genie に使わせる **Gold / Silver** テーブルにコメントを付けます。
# MAGIC
# MAGIC > Genie 精度の優先順位: **SQL式 > サンプルSQL > テキスト指示**。その土台がテーブル・カラムコメントです。

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============ gold_monthly_engagement ============
# MAGIC COMMENT ON TABLE gold_monthly_engagement IS '月別・カテゴリ別の記事エンゲージメント集計。記事閲覧数・読了数・読了率・ユニーク読者数。';
# MAGIC ALTER TABLE gold_monthly_engagement ALTER COLUMN ym COMMENT '年月（yyyy-MM形式、例: 2025-07）。「いつ」「月」の軸。';
# MAGIC ALTER TABLE gold_monthly_engagement ALTER COLUMN category COMMENT '記事カテゴリ（経済、政治、ビジネス、マーケット、テクノロジー、国際、オピニオン、スポーツ）';
# MAGIC ALTER TABLE gold_monthly_engagement ALTER COLUMN article_views COMMENT '記事を開いた回数（read_start + read_complete）。「閲覧数」「PV」と同義。';
# MAGIC ALTER TABLE gold_monthly_engagement ALTER COLUMN reads_completed COMMENT '最後まで読まれた回数（読了数）。';
# MAGIC ALTER TABLE gold_monthly_engagement ALTER COLUMN unique_readers COMMENT 'ユニーク読者数（記事を読んだ会員の人数）。';
# MAGIC ALTER TABLE gold_monthly_engagement ALTER COLUMN completion_rate COMMENT '読了率（%）= 読了数 / 閲覧数 × 100。「読了率」と同義。';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============ gold_member_segment ============
# MAGIC COMMENT ON TABLE gold_member_segment IS '会員ごとの行動サマリー。プラン・年代・利用頻度セグメント・ペイウォール接触・課金回数など。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN plan_type COMMENT '会員プラン（free=無料会員、paid=有料会員、premium=プレミアム会員）。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN age_group COMMENT '年代（20代以下、30代、40代、50代、60代以上）。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN total_events COMMENT '行動ログの総数（利用頻度の指標）。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN reads_completed COMMENT 'その会員の読了数。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN paywall_hits COMMENT 'その会員のペイウォール接触回数。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN conversions COMMENT 'その会員の課金（subscribe）回数。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN last_event_date COMMENT '最後に行動した日。離脱リスク判定に使う。';
# MAGIC ALTER TABLE gold_member_segment ALTER COLUMN activity_segment COMMENT '利用頻度セグメント（ヘビーリーダー、通常、ライト、休眠）。';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============ gold_paywall_conversion ============
# MAGIC COMMENT ON TABLE gold_paywall_conversion IS '年月・年代別のペイウォール接触から課金への転換集計。課金導線の分析に使う。';
# MAGIC ALTER TABLE gold_paywall_conversion ALTER COLUMN ym COMMENT '年月（yyyy-MM形式）。';
# MAGIC ALTER TABLE gold_paywall_conversion ALTER COLUMN age_group COMMENT '年代（20代以下、30代、40代、50代、60代以上）。';
# MAGIC ALTER TABLE gold_paywall_conversion ALTER COLUMN paywall_hits COMMENT 'ペイウォール接触回数（無料会員が有料記事の壁に当たった回数）。';
# MAGIC ALTER TABLE gold_paywall_conversion ALTER COLUMN conversions COMMENT '課金転換回数（ペイウォールから有料会員になった回数）。';
# MAGIC ALTER TABLE gold_paywall_conversion ALTER COLUMN conversion_rate COMMENT '転換率（%）= 課金転換 / ペイウォール接触 × 100。「転換率」と同義。';

# COMMAND ----------

# MAGIC %sql
# MAGIC -- ============ silver_subscriptions（解約分析用）============
# MAGIC COMMENT ON TABLE silver_subscriptions IS '購読履歴。有料/プレミアム会員の契約開始・解約・ステータス。churn（解約）分析に使う。';
# MAGIC ALTER TABLE silver_subscriptions ALTER COLUMN plan_type COMMENT '会員プラン（paid=有料会員、premium=プレミアム会員）。';
# MAGIC ALTER TABLE silver_subscriptions ALTER COLUMN start_date COMMENT '契約開始日。';
# MAGIC ALTER TABLE silver_subscriptions ALTER COLUMN end_date COMMENT '解約日。継続中（active）の場合は NULL。';
# MAGIC ALTER TABLE silver_subscriptions ALTER COLUMN status COMMENT '購読ステータス（active=継続中、churned=解約済み）。「解約」は status=churned を指す。';
# MAGIC ALTER TABLE silver_subscriptions ALTER COLUMN churn_ym COMMENT '解約した年月（yyyy-MM形式）。解約済みのみ。';
# MAGIC ALTER TABLE silver_subscriptions ALTER COLUMN tenure_days COMMENT '契約日数（開始から解約までの日数）。';

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Genie Space を作成する（UI操作）
# MAGIC
# MAGIC | # | 操作 |
# MAGIC |---|---|
# MAGIC | 1 | 左サイドバー → **Genie** → **「New」/「Genie スペースを作成」** |
# MAGIC | 2 | **テーブルを追加**: `gold_monthly_engagement`, `gold_member_segment`, `gold_paywall_conversion`, `silver_subscriptions` を選択 |
# MAGIC | 3 | 名前: `202606_handson_<苗字>` |
# MAGIC | 4 | SQL Warehouse: デフォルトを選択 |

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: まずはメタデータだけで質問してみる（Instructions なし）
# MAGIC
# MAGIC `04_analysis` で手こずった問いを、そのまま日本語で投げてみましょう。
# MAGIC
# MAGIC | # | 質問 | 期待 |
# MAGIC |---|---|---|
# MAGIC | 1 | 月別の解約件数を教えて | 2025年後半に増加 |
# MAGIC | 2 | 解約が多い年代は？ | 20代以下が多い |
# MAGIC | 3 | テクノロジーの読了率は2025年後半どうなった？ | 急落が見える |
# MAGIC | 4 | ペイウォール接触が多いのに転換率が低い年代は？ | 30代 |
# MAGIC | 5 | **サイレント離脱は何人いる？** | ?? メタデータに定義がないので答えられない |
# MAGIC
# MAGIC > 質問1〜4は、`04` で苦労したクエリが**一瞬**で返ってくるはずです。
# MAGIC > 質問5「サイレント離脱」は社内用語なので、次の Instructions で解決します。

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Instructions で社内用語を教える
# MAGIC
# MAGIC Genie Space の **設定（⚙️）→ 指示（Instructions）** の **テキスト** に以下を貼り付けてください。

# COMMAND ----------

# MAGIC %md
# MAGIC ```
# MAGIC あなたはニュース電子版（デジタル購読）サービスのデータアナリストです。日本語で回答してください。
# MAGIC
# MAGIC - プラン: free=無料会員、paid=有料会員、premium=プレミアム会員
# MAGIC - 「読了率」は gold_monthly_engagement の completion_rate を指す
# MAGIC - 「転換率」は gold_paywall_conversion の conversion_rate を指す
# MAGIC - 「解約」「churn」は silver_subscriptions の status='churned' を指す。解約月は churn_ym。
# MAGIC - 「ヘビーリーダー」は gold_member_segment の activity_segment='ヘビーリーダー' を指す
# MAGIC - 年月は yyyy年MM月 形式で表示し、グラフはカテゴリ/年代ごとに色分けすること
# MAGIC
# MAGIC ★ 社内用語:
# MAGIC - 「サイレント離脱」= 有料会員（plan_type が paid または premium）のうち、まだ解約していない（subscriptions に churned がない）が、
# MAGIC   最後の行動（gold_member_segment.last_event_date）からデータ上の最新日まで90日以上経過している会員。離脱予備軍。
# MAGIC - 「課金導線の改善ターゲット」= ペイウォール接触が多いのに転換率が低い年代。
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Instructions 追加後に再テスト
# MAGIC
# MAGIC | # | 質問 | 期待 |
# MAGIC |---|---|---|
# MAGIC | 5 | **サイレント離脱は何人いる？** | ✅ 今度は定義に沿って答えられる |
# MAGIC | 6 | サイレント離脱が多い年代とプランは？ | ✅ 深掘りもできる |
# MAGIC
# MAGIC > **体験のポイント**: メタデータだけでは答えられなかった社内用語が、Instructions を足すだけで正しく答えられるようになりました。
# MAGIC > 意図と違う SQL が生成されたら Instructions を調整する。これが **Genie Space のチューニング** です。

# COMMAND ----------

# MAGIC %md
# MAGIC ## まとめ
# MAGIC
# MAGIC - `04` で手こずった分析が、Genie Space では **日本語の質問だけ**で返ってきた
# MAGIC - コメント（メタデータ）と Instructions が精度の土台
# MAGIC - これを業務部門（編集・マーケ・経営企画）に渡せば、**非エンジニアでもセルフ分析**できる ← ここは講師が事例で補足
# MAGIC
# MAGIC お疲れさまでした！ さらに興味があれば、`99_extra_cost`（コスト分析）を持ち帰りで試してみてください。
