# Databricks notebook source
# MAGIC %md
# MAGIC # セットアップ — デジタル購読サービス サンプルデータ生成
# MAGIC
# MAGIC このノートブックを **最初に1回だけ** 実行してください。
# MAGIC ニュース電子版（デジタル購読）サービスの模擬データを生成し、**Bronze テーブル**として
# MAGIC あなたのスキーマに直接登録します。
# MAGIC
# MAGIC **所要時間:** 約2分
# MAGIC
# MAGIC | テーブル | 内容 | 件数目安 |
# MAGIC |---|---|---|
# MAGIC | `bronze_members` | 会員マスタ（無料 / 有料 / プレミアム） | 1,000人 |
# MAGIC | `bronze_articles` | 記事マスタ（カテゴリ・有料記事フラグ） | 200本 |
# MAGIC | `bronze_reading_logs` | 行動ログ（閲覧・読了・ペイウォール・課金） | 約11,000件 |
# MAGIC | `bronze_subscriptions` | 購読履歴（開始・解約・ステータス） | 約320件 |
# MAGIC
# MAGIC > **Bronze の考え方**：データは加工せず「生のまま」Delta 化します。日付なども文字列のまま登録し、
# MAGIC > 型変換や加工は後続の Silver で行います。

# COMMAND ----------

# MAGIC %md
# MAGIC ## 環境設定
# MAGIC
# MAGIC `00_env` で設定したカタログ・スキーマを使用します。まだ変更していない場合は、先に `00_env` を開いて設定してください。

# COMMAND ----------

# MAGIC %run ./00_env

# COMMAND ----------

# MAGIC %md
# MAGIC ## データ生成
# MAGIC
# MAGIC 以下は変更不要です。そのまま実行してください。
# MAGIC `random.seed(42)` で固定しているため、誰が実行しても同じデータが生成されます。

# COMMAND ----------

import random
from datetime import date, datetime, timedelta

random.seed(42)

LOG_START = date(2024, 1, 1)
LOG_END   = date(2025, 12, 31)
SPAN_DAYS = (LOG_END - LOG_START).days

# ── マスタ用の語彙 ───────────────────────────────────────────────
LAST_NAMES = ["佐藤","鈴木","高橋","田中","伊藤","渡辺","山本","中村","小林","加藤",
              "吉田","山田","佐々木","松本","井上","木村","林","斉藤","清水","山口"]
FIRST_NAMES_M = ["太郎","健太","翔太","大輝","拓海","蓮","悠真","大和","直樹","隆"]
FIRST_NAMES_F = ["花子","さくら","美咲","陽菜","結衣","凛","芽依","杏","莉子","真由"]
PREFECTURES = ["東京都","大阪府","神奈川県","愛知県","埼玉県","千葉県","福岡県","北海道","兵庫県","京都府"]
OCCUPATIONS = ["会社員","経営者・役員","公務員","自営業","専門職","学生","その他"]
CATEGORIES  = ["経済","政治","ビジネス","マーケット","テクノロジー","国際","オピニオン","スポーツ"]

# ── 会員マスタ（1,000人）─────────────────────────────────────────
# plan_type: free（無料会員）/ paid（有料会員）/ premium（有料の上位プラン）
members = []
for mid in range(1, 1001):
    gender = random.choice(["M", "F"])
    name = random.choice(LAST_NAMES) + " " + random.choice(FIRST_NAMES_M if gender == "M" else FIRST_NAMES_F)
    age = random.randint(18, 70)
    pref = random.choice(PREFECTURES)
    occ = random.choices(OCCUPATIONS, weights=[50, 8, 8, 8, 12, 8, 6])[0]

    r = random.random()
    if r < 0.68:
        plan = "free"
    elif r < 0.94:
        plan = "paid"
    else:
        plan = "premium"

    reg_date = date(2022, 6, 1) + timedelta(days=random.randint(0, 910))  # ~2022-06 〜 2024-12
    email = f"member{mid}@example.com"
    members.append((mid, name, age, gender, pref, occ, plan, str(reg_date), email))

# ── 記事マスタ（200本）──────────────────────────────────────────
# is_premium = 1 の記事は、無料会員が読もうとするとペイウォールに当たる
articles = []
article_meta = {}  # article_id -> (category, is_premium, publish_date)
for aid in range(1, 201):
    cat = random.choice(CATEGORIES)
    is_premium = 1 if random.random() < 0.45 else 0
    pub = LOG_START + timedelta(days=random.randint(0, SPAN_DAYS))
    title = f"【{cat}】解説記事 No.{aid}"
    articles.append((aid, title, cat, str(pub), is_premium))
    article_meta[aid] = (cat, is_premium, pub)

# ── 行動ログ（reading_logs）──────────────────────────────────────
# event_type:
#   read_start    … 記事を開いたが読了せず離脱
#   read_complete … 最後まで読んだ（読了）
#   paywall_hit   … 無料会員が有料記事の壁に当たった
#   subscribe     … ペイウォールから有料会員に転換した（課金）
logs = []
log_id = 1
member_plan = {m[0]: m[6] for m in members}
member_age  = {m[0]: m[2] for m in members}
member_reg  = {m[0]: date.fromisoformat(m[7]) for m in members}

for mid in range(1, 1001):
    plan = member_plan[mid]
    age = member_age[mid]
    reg = member_reg[mid]

    # エンゲージメント水準で閲覧回数を決める
    er = random.random()
    if er < 0.10:
        n_events = random.randint(25, 45)   # ヘビーリーダー
    elif er < 0.60:
        n_events = random.randint(8, 20)    # 通常
    elif er < 0.90:
        n_events = random.randint(2, 7)     # ライト
    else:
        n_events = random.randint(0, 1)     # 休眠

    for _ in range(n_events):
        aid = random.randint(1, 200)
        cat, is_premium, pub = article_meta[aid]
        earliest = max(pub, reg)
        if earliest > LOG_END:
            continue
        et = earliest + timedelta(days=random.randint(0, (LOG_END - earliest).days))
        event_time = datetime(et.year, et.month, et.day, random.randint(0, 23), random.randint(0, 59))
        device = random.choices(["web", "app"], weights=[55, 45])[0]

        if is_premium == 1 and plan == "free":
            # ── ペイウォール接触 ──
            logs.append((log_id, mid, aid, "paywall_hit", str(event_time), device,
                         random.randint(5, 40), random.randint(10, 40)))
            log_id += 1
            # 転換（subscribe）。30〜45歳の無料会員はペイウォールには多く当たるが転換しにくい（=改善余地の仕込み）
            conv = 0.02 if 30 <= age <= 45 else 0.10
            if random.random() < conv:
                st = event_time + timedelta(minutes=random.randint(1, 30))
                logs.append((log_id, mid, aid, "subscribe", str(st), device, 0, 0))
                log_id += 1
        else:
            # ── 通常の閲覧（読了 or 離脱）──
            comp = 0.70 if plan in ("paid", "premium") else 0.55
            # テクノロジーカテゴリは2025年後半に読了率が低下（=エンゲージメント低下の仕込み）
            if cat == "テクノロジー" and event_time.date() >= date(2025, 7, 1):
                comp *= 0.5
            if random.random() < comp:
                logs.append((log_id, mid, aid, "read_complete", str(event_time), device,
                             random.randint(120, 600), random.randint(80, 100)))
            else:
                logs.append((log_id, mid, aid, "read_start", str(event_time), device,
                             random.randint(10, 90), random.randint(15, 60)))
            log_id += 1

# ── 購読履歴（subscriptions）────────────────────────────────────
# 有料/プレミアム会員に購読レコードを作成。20代は2025年後半に解約が集中（=解約スパイクの仕込み）
subscriptions = []
sub_id = 1
for mid in range(1, 1001):
    plan = member_plan[mid]
    if plan not in ("paid", "premium"):
        continue
    age = member_age[mid]
    reg = member_reg[mid]
    start = reg + timedelta(days=random.randint(0, 120))
    if start > LOG_END:
        start = reg

    young = age < 30
    churn_p = 0.35 if young else 0.13
    if random.random() < churn_p:
        if young:
            end = date(2025, 7, 1) + timedelta(days=random.randint(0, 180))  # H2 2025 に集中
        else:
            end = start + timedelta(days=random.randint(90, 600))
        if end > LOG_END:
            end = LOG_END
        if end <= start:
            end = start + timedelta(days=30)
        subscriptions.append((sub_id, mid, plan, str(start), str(end), "churned"))
    else:
        subscriptions.append((sub_id, mid, plan, str(start), "", "active"))
    sub_id += 1

print(f"members:       {len(members):,} 件")
print(f"articles:      {len(articles):,} 件")
print(f"reading_logs:  {len(logs):,} 件")
print(f"subscriptions: {len(subscriptions):,} 件")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze テーブルとして Unity Catalog に登録
# MAGIC
# MAGIC 生成したデータを、そのまま **Bronze テーブル**（生データ層）として Unity Catalog に登録します。
# MAGIC 日付などは文字列のまま保存し、型変換は後続の `03a_silver` で行います。
# MAGIC
# MAGIC 次の `02_explore_uc` では、ここで作った4つの `bronze_*` テーブルをカタログから探索します。

# COMMAND ----------

from pyspark.sql.types import (StructType, StructField, IntegerType, StringType)

members_schema = StructType([
    StructField("member_id", IntegerType()), StructField("name", StringType()),
    StructField("age", IntegerType()), StructField("gender", StringType()),
    StructField("prefecture", StringType()), StructField("occupation", StringType()),
    StructField("plan_type", StringType()), StructField("registration_date", StringType()),
    StructField("email", StringType()),
])
articles_schema = StructType([
    StructField("article_id", IntegerType()), StructField("title", StringType()),
    StructField("category", StringType()), StructField("publish_date", StringType()),
    StructField("is_premium", IntegerType()),
])
logs_schema = StructType([
    StructField("log_id", IntegerType()), StructField("member_id", IntegerType()),
    StructField("article_id", IntegerType()), StructField("event_type", StringType()),
    StructField("event_time", StringType()), StructField("device", StringType()),
    StructField("reading_seconds", IntegerType()), StructField("scroll_depth", IntegerType()),
])
subs_schema = StructType([
    StructField("subscription_id", IntegerType()), StructField("member_id", IntegerType()),
    StructField("plan_type", StringType()), StructField("start_date", StringType()),
    StructField("end_date", StringType()), StructField("status", StringType()),
])

def register_bronze(name, rows, schema_def):
    df = spark.createDataFrame(rows, schema_def)
    (df.write.format("delta").mode("overwrite")
       .option("overwriteSchema", "true")
       .saveAsTable(f"{catalog}.{schema}.bronze_{name}"))
    print(f"  bronze_{name}: {df.count():,} rows")

register_bronze("members", members, members_schema)
register_bronze("articles", articles, articles_schema)
register_bronze("reading_logs", logs, logs_schema)
register_bronze("subscriptions", subscriptions, subs_schema)

print("\n4つの Bronze テーブルを Unity Catalog に登録しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Genie / AIアシスタントの日本語化
# MAGIC
# MAGIC ノートブック内蔵の AIアシスタント（Genie Code）が日本語で回答するよう設定します。

# COMMAND ----------

import os
folder = "/Workspace" + "/".join(
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get().rsplit("/", 1)[:-1]
)
with open(os.path.join(folder, "AGENTS.md"), "w") as f:
    f.write("""# Genie Code Instructions
- 必ず日本語で回答してください
- コード内のコメントも日本語で書いてください
""")
print("AGENTS.md を作成しました")

# COMMAND ----------

# MAGIC %md
# MAGIC ## セットアップ完了
# MAGIC
# MAGIC Unity Catalog に 4つの Bronze テーブル（`bronze_members` / `bronze_articles` / `bronze_reading_logs` / `bronze_subscriptions`）が作成されました。
# MAGIC
# MAGIC **次のステップ:** `02_explore_uc` を開き、Unity Catalog でデータを探索しましょう。
