# Lawsy（法令RAGアプリ）深掘り調査

- **調査日:** 2026-07-08
- **対象:** `genai-ai-api/google-cloud/lawsy-custom-bq`
- **ステータス:** 完了（OxigenAIの再実装から逆解析）

---

## 概要

Lawsyは源内AIアプリの中で最も完成度が高い行政実務用AIアプリ。
e-Gov（法令データベース）から最新の法律条文を取得し、RAGで回答する法制度AIアプリ。

公式READMEへの直接アクセスが制限されていたため、Lawsyを**Pure Rustで再実装したOxigenAI**（cool-japan/oxigenai）のドキュメントから内部構造を逆解析した。

参照元: https://github.com/cool-japan/oxigenai

---

## Lawsyの技術スタック

| レイヤー | 技術 |
|---|---|
| 言語 | Python |
| クラウド | Google Cloud（GCP） |
| LLM | Vertex AI Gemini |
| ベクトル検索 | BigQuery VECTOR_SEARCH |
| 法令データ | e-Gov 法令XML |
| IaC | Terraform |

---

## 処理パイプライン（OxigenAIの再実装から解析）

```
[ ユーザーの質問 ]
    ↓
1. 法令名推定（Gemini + Web検索グラウンディング）
    ↓
2. BigQuery VECTOR_SEARCH（e-Gov法令XMLをベクトル化して検索）
    ↓
3. 条文選択（AIが関連条文を絞り込み）
    ↓
4. レポート生成（Gemini）
    ↓
5. 出典付き最終レポート出力
```

---

## 源内APIプロトコルとの対応

OxigenAIのAPIは源内プロトコルに完全準拠している。
以下のリクエスト/レスポンスが源内WebからLawsyに送られる形式：

**リクエスト（源内Web → Lawsy）**
```json
{
  "inputs": {
    "input_text": "個人情報保護法の「個人情報」の定義について教えてください"
  }
}
```

**レスポンス（Lawsy → 源内Web）**
```json
{
  "outputs": "# 個人情報保護法における「個人情報」の定義\n\n...\n\n## 出典\n[1] 【e-laws公式条文】..."
}
```

シンプル。`input_text` 1つを受け取り、Markdownのレポートを返すだけ。

---

## BigQueryのデータ構造（推定）

e-Gov法令XMLをBigQueryに格納してVECTOR_SEARCHで検索する構成。

```
BQ_DATASET_ID: e_laws_search（デフォルト）

推定スキーマ:
- law_id: STRING（法令ID）
- law_title: STRING（法令名）
- article_num: STRING（条番号）
- article_text: STRING（条文テキスト）
- embedding: ARRAY<FLOAT64>（ベクトル埋め込み）
- source_url: STRING（e-Gov URL）
```

---

## 環境変数（OxigenAIから逆解析）

```bash
# GCP設定（必須）
GOOGLE_CLOUD_PROJECT=your-project-id
INFERENCE_PROJECT_ID=your-inference-project-id
INFERENCE_LOCATION=asia-northeast1

# Gemini設定
MODEL_ID=gemini-2.5-flash
GENERATION_TEMPERATURE=0.5

# BigQuery設定
BQ_DATASET_ID=e_laws_search

# 任意
GCS_BUCKET_NAME=your-bucket
LOG_LEVEL=INFO
```

---

## Lawsyを参考にした自作RAGアプリの作り方

Lawsyの設計を参考に、**任意のドキュメントをRAG化して源内に登録できる**。

### 最小構成（Python + FastAPI）

```python
from fastapi import FastAPI
from pydantic import BaseModel
import vertexai
from vertexai.generative_models import GenerativeModel

app = FastAPI()

class Inputs(BaseModel):
    input_text: str

class Request(BaseModel):
    inputs: Inputs

@app.post("/")
async def query(req: Request):
    # 1. ベクトル検索でドキュメントを取得
    docs = vector_search(req.inputs.input_text)
    
    # 2. LLMでレポート生成
    model = GenerativeModel("gemini-2.5-flash")
    prompt = f"以下の資料を参考に回答してください。\n\n{docs}\n\n質問: {req.inputs.input_text}"
    response = model.generate_content(prompt)
    
    return {"outputs": response.text}
```

これだけで源内WebのGUIから登録できる最小RAGアプリが完成。

---

## OxigenAI（Lawsyの非公式Rust再実装）について

調査中に発見した注目プロジェクト。

- **リポジトリ:** https://github.com/cool-japan/oxigenai
- **概要:** Lawsyを Pure Rust + 形式検証で再実装
- **特徴:**
  - 源内APIプロトコルと完全互換
  - OxiZ SMTソルバーによる法令間の論理矛盾検出
  - GCP不要のオフライン版（商用）も開発中
  - `cargo install oxigenai` でインストール可能

**注目点:** 源内互換APIをRustで実装しているので、**Lawsyの代替として源内Webに登録できる可能性がある**。

```bash
# OxigenAIを試す場合
cargo install oxigenai
oxigenai serve  # localhost:8080 で起動
# → 源内WebのGUIで http://localhost:8080 を登録すれば動く（はず）
```

> **TODO:** OxigenAIを実際に源内Webに登録して動作確認する

---

## VPS環境での展開可能性

Lawsyの構成を分析すると、**GCPなしでも動かせる可能性がある**。

| コンポーネント | GCP版 | VPS版（代替案） |
|---|---|---|
| LLM | Vertex AI Gemini | Ollama + ローカルLLM |
| ベクトルDB | BigQuery | pgvector / Qdrant / Chroma |
| 法令データ | e-Gov API | e-Gov APIから取得してローカル保存 |
| API サーバー | Cloud Run / GCE | コンテナ（Docker/LXC） |

**結論:** GCP依存を剥がしてVPS上のコンテナで動かすことは技術的に可能。

---

## 今後の調査事項

> **TODO:** Lawsy公式READMEを直接確認する（GitHubのbot制限を回避して）
> **TODO:** e-Gov法令APIの仕様を調査する（データ取得フロー）
> **TODO:** BigQueryのembedding生成方法を確認する（Vertex AI Embeddings API？）
> **TODO:** OxigenAIをローカルで動かして源内プロトコル互換性を検証する
> **TODO:** pgvector + OllamaでLawsy相当のRAGをVPS上に構築できるか検証する
