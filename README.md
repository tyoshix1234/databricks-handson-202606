# Databricks ハンズオン（202606）— Lakehouse 入門

ニュース電子版（デジタル購読）サービスのデータを題材に、**Unity Catalog → Lakeflow Jobs → Genie Space** を手を動かして体験する Databricks ハンズオンです（想定 100〜120分）。

## ⬇️ ダウンロード（1クリック）

▶ **[handson_202606.dbc をダウンロード](https://github.com/tyoshix1234/databricks-handson-202606/releases/download/v1/handson_202606.dbc)**

## Databricks へのインポート手順

1. 上のリンクから `handson_202606.dbc` をダウンロード
2. Databricks ワークスペースで、任意のフォルダを右クリック → **インポート**
3. **ファイル** を選び、ダウンロードした `.dbc` をアップロード
4. `handson_202606` フォルダがノートブックごと展開されます

## 進め方

| # | ノートブック | 内容 |
|---|---|---|
| 00 | `00_env` | カタログ（固定）＋自分のスキーマを設定。最初に開く |
| 01 | `01_setup` | データ生成 → UC に `bronze_*` 4テーブルを直接登録 |
| 02 | `02_explore_uc` | UC探索＋AI説明文サジェスト＋簡単な集計 |
| 03a | `03a_silver` | bronze → silver_*（コード確認のみ・実行しない） |
| 03b | `03b_gold` | silver → gold_* マート（コード確認のみ・実行しない） |
| 03c | `03c_create_job` | Lakeflow Job をUIで手動作成・実行（silver→gold） |
| 04 | `04_analysis` | churn 等を自力で分析（手こずる体験） |
| 05 | `05_genie_space` | 同じ問いを Genie Space で（一気に楽になる体験） |
| 99 | `99_extra_cost` | system テーブルでコスト分析（持ち帰り/任意） |

## 事前準備（講師・管理者）

- 共有カタログ `handson_202606`（または任意名）を作成し、受講者にスキーマ作成権限を付与
- サーバレス / SQL Warehouse を有効化
- `00_env` で `catalog`（固定）と `schema`（各自の名前）を設定

## 中身

- `handson_202606/` … ノートブックのソース（`.py`、`# Databricks notebook source` 形式）
- `handson_202606.dbc` … Databricks インポート用アーカイブ（リリース資産と同じもの）

`random.seed(42)` 固定のため、誰が実行しても同じサンプルデータが生成されます。
