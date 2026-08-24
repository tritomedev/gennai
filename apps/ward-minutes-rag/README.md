# ward-minutes-rag（港区 議事録RAG Ex-App / POC）

- **作成日:** 2026-07-10
- **ステータス:** サンプルデータ整備フェーズ（TASK-033）
- **関連:**
  - ユースケース: [../../docs/05_customization/usecase-ward-minutes-rag.md](../../docs/05_customization/usecase-ward-minutes-rag.md)
  - スクレイピング設計: [../../docs/05_customization/minato-scraping-design.md](../../docs/05_customization/minato-scraping-design.md)

## 目的

港区を対象に、区民が「子どもの補助金について何かないか」と自然言語で尋ねると、
以下2段で回答する源内 Ex-App（自作AIアプリ）のPOC。

1. **AsIs（現行制度）** … 区民向けサイトの子育て・補助金ページから現在使える制度
2. **議論中／今後の方針** … 議会で語られた今後の施策・拡充予定

## 現在のスコープ（重要）

- **まずは「小さな実データのサンプルデータセット」を用意する**段階（TASK-033）。
  RAG Ex-App の価値証明に必要なのは数十チャンクの実データで十分、という判断。
- **議事録の自動スクレイピング（gikai2 の旧式ASP・セッション駆動）は本POCでは行わない**。
  ここは最難所（[設計書](../../docs/05_customization/minato-scraping-design.md) 参照）で、
  価値証明の後に別タスクで着手する。

## ディレクトリ構成

```
ward-minutes-rag/
├── scripts/
│   ├── fetch_seido.py    # (A) 現行制度ページを取得・本文抽出 → seido.jsonl（自動）
│   ├── build_giron.py    # (B) 議論中/今後の方針を手キュレーション → giron.jsonl
│   ├── ingest_qdrant.py  # チャンク分割＋Bedrock埋め込み → Qdrant投入（TASK-007）
│   └── search_test.py    # 検索動作の確認（Ex-Appの検索コアの原型）
├── data/
│   ├── raw/urls.tsv      # (A) の取得対象URL一覧（制度名/slug/パス）
│   ├── raw/*.html        # (A) の生HTML（gitignore）
│   └── sample/*.jsonl    # 生成サンプルデータ（gitignore）
├── .venv/                # Python仮想環境（gitignore）
└── .gitignore            # data配下の港区本文はコミットしない（二次利用回避）
```

> **注意（著作権）:** `data/` 配下は港区サイト/議会の本文を含むため gitignore 済み。
> 二次利用規約は「無断転載禁止」であり（[ユースケース文書](../../docs/05_customization/usecase-ward-minutes-rag.md) 参照）、
> 本POCは社内検証・ローカル閉環境限定で扱う。公開サービス化には区の利用許諾が前提。

## サンプルデータのスキーマ

共通フィールド: `id` / `source_type` / `title` / `text` / `url` / `ward`。

- **seido.jsonl（source_type=`seido`, 11件）** … 現行制度。`seido_name` `updated`（ページ更新日）`fetched_at`。
  - 出典: 港区公式サイト 子育て・手当/助成 各制度ページ（静的HTML・UTF-8）。
  - 生成: `python3 scripts/fetch_seido.py`
- **giron.jsonl（source_type=`giron`, 13件）** … 議論中/今後の方針。`planned_time` `source` `session` `session_date` `curation=manual`。
  - 出典: 令和8年第1回港区議会定例会 区長所信表明「重点的に取り組む5つの施策」。
  - 生成: `python3 scripts/build_giron.py`（手キュレーション、原文表現を引用）

RAGでは `source_type` で回答の2段（AsIs / 議論中）を出し分ける。
チャンクは当面「1レコード=1チャンク」を基本とし、長い制度ページのみ見出しで分割する。

## ベクトルDB（TASK-007・完了）

- **Qdrant**: Docker で起動（コンテナ名 `gennai-qdrant`, ポート 6333/6334）。
- **埋め込み**: Bedrock `cohere.embed-multilingual-v3`（1024次元, ap-northeast-1）。
  日本語に強く、`search_document` / `search_query` を撃ち分けられる（非対称検索）ため採用。
- **コレクション**: `minato_kosodate`（Cosine距離）。24レコード → **106チャンク**（seido=93 / giron=13）。

```bash
# Qdrant 起動（初回）
docker run -d --name gennai-qdrant -p 6333:6333 -p 6334:6334 \
  -v gennai-qdrant-storage:/qdrant/storage qdrant/qdrant:latest
```

### 実装で判明した重要な知見

1. **チャンク分割は必須**
   Cohere embed-multilingual-v3 の入力上限は **512トークン**。制度ページ本文は最大約8,000文字あり、
   分割せず投げると大半が切り捨てられて検索に載らない。行境界を尊重した ~400文字チャンクに分割している。

2. **doc_id でのグループ化が必須**（検索品質の要）
   グループ化しないと、**チャンク数の多い長い制度ページが上位を独占**する。
   実測では「子どもの補助金についてなにか無いかな？」に対しトップ5が全て「子ども医療費助成」の
   断片で埋まり、児童手当等が出てこなかった。Qdrant の `query_points_groups(group_by="doc_id")` で
   束ねることで、5件バラバラの制度が返るようになった。

3. **グループ内の最高スコアのチャンク＝説明として最適とは限らない**
   例：児童育成手当では所得制限の数表チャンク、児童手当では公務員向けの注意書きチャンクが最上位になる。
   → Ex-App（TASK-034）では、グループ内の複数チャンクをLLMに渡して合成させる／
   `chunk_index=0`（導入部）を優先する、といった対処が要る。

## 再生成手順

```bash
cd apps/ward-minutes-rag
python3 scripts/fetch_seido.py           # (A) 現行制度 → data/sample/seido.jsonl
python3 scripts/build_giron.py           # (B) 議論中   → data/sample/giron.jsonl
.venv/bin/python scripts/ingest_qdrant.py  # チャンク化＋埋め込み → Qdrant
.venv/bin/python scripts/search_test.py "子どもの補助金についてなにか無いかな？"
```

> 依存（boto3 / qdrant-client）は `.venv` に隔離。AWS認証情報とBedrockのモデルアクセスが前提。

## Ex-App本体（TASK-034・ローカル動作確認まで完了）

- `rag.py` … 検索＋回答生成のコア（`main.py` と `scripts/search_test.py` で共用）
- `main.py` … 源内プロトコル準拠のFastAPIガワ（`POST /` で `{"inputs":{...}}` → `{"outputs":"Markdown"}`）
- **LLM**: Bedrock `amazon.nova-lite-v1:0`（環境変数 `LLM_MODEL` で差し替え可）
  - **Claude系（claude-3-haiku / claude-3-5-sonnet）はモデルアクセス未有効でアクセス拒否**。
    Bedrockコンソールで有効化すれば `LLM_MODEL` を変えるだけで切替できる。

```bash
# 起動
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001

# 源内プロトコルでのリクエスト
curl -X POST http://127.0.0.1:8001/ -H "Content-Type: application/json" \
  -d '{"inputs":{"input_text":"子どもの補助金についてなにか無いかな？","conversation_history":""}}'
```

### 源内Webへの登録設定（JSON）

```json
{
  "input_text": {
    "title": "知りたいこと",
    "desc": "例）子どもの補助金についてなにか無いかな？",
    "type": "textarea",
    "required": true
  },
  "conversation_history": { "title": "会話履歴", "type": "textarea" }
}
```

### 動作確認の結果（2026-07-13）

- `POST /` が HTTP 200 / 約2秒で2段構えのMarkdownを返すことを確認。
- **幻覚なしを実データで検証済み**：回答中の「対象児童一人につき2万円」「0歳から高校生年代」等が
  取得元の原文に実在することを確認（プロンプトのグラウンディング制約が機能している）。
- URLはLLMに書かせず payload から機械的に出力しているため、出典リンクの幻覚は構造的に発生しない。

### 既知の課題（次の改善candidates）

1. **スコア閾値がない** … 関連する制度が無い質問でも常に上位5件を返すため、
   無関係な制度が回答に混ざる。実測：「保育園の一時預かりの支援は？」に対し、
   サンプルに該当制度が無いにもかかわらず児童手当・子どもタクシー券等が提示された。
   → 最低スコアの閾値を設けて「該当なし」と正直に返せるようにする。
2. **出典セクションが引用されなかったソースも列挙する** … LLMが本文で触れなかった
   ソースも出典に並ぶ。→ 回答本文中のタグ（[S1] 等）を拾って出典を絞り込む。
3. **サンプルデータの薄さ** … 制度11件のみ。一時保育・保育料など未収録の領域がある。

## 次のステップ

1. **源内Webへの登録・実機確認**（TASK-034の残り）
   … ローカル起動のままでは源内Webから到達できないため、公開ホストが必要（TASK-030と同じ論点）
2. 上記「既知の課題」1・2の改善
3. （後回し）議事録ASPセッション攻略による本格スクレイパ（TASK-036）
