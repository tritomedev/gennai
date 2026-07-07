# genai-ai-api 調査ログ

- **調査日:** 2026-07-08
- **対象リポジトリ:** https://github.com/digital-go-jp/genai-ai-api
- **最新リリース:** v1.0.3（2026年4月24日）
- **ステータス:** 調査中

---

## リポジトリ概要

源内で動く行政実務用AIアプリ群のマイクロサービス実装。ガバメントクラウドに採択された各クラウドサービス（AWS / Azure / GCP）ごとにアプリが分かれている。

**言語構成:** Python 44.1% / Bicep 25.1% / TypeScript 24.6% / HCL 2.9% / JavaScript 2.7% / Shell 0.3% / PowerShell 0.3%

---

## ディレクトリ構成

```
genai-ai-api/
├── aws/
│   └── query-expansion-rag/     # RAG開発テンプレート
├── azure/
│   └── genai-azure/             # LLMセルフデプロイテンプレート
├── google-cloud/
│   └── lawsy-custom-bq/         # 法令RAGアプリ（BigQuery連携）
├── biome.json                   # リンター/フォーマッター設定
├── mise.toml                    # Node/Pythonバージョン管理
├── pyproject.toml               # Python依存関係
└── package.json                 # Node依存関係
```

---

## 公開AIアプリ詳細

### 1. AWS: Query Expansion RAG（検索拡張生成テンプレート）

- **パス:** `aws/query-expansion-rag/`
- **用途:** RAGアプリの開発テンプレート
- **技術:** Python / AWS CDK / AWS Bedrock
- **特徴:** クエリ拡張（Query Expansion）を使って検索精度を高めるRAGの実装例

> **TODO:** 具体的な実装内容・使用モデルを調査する

### 2. Azure: LLMセルフデプロイテンプレート

- **パス:** `azure/genai-azure/`
- **用途:** Azure上でLLMをセルフデプロイして利用する開発テンプレート
- **技術:** TypeScript / Bicep（Azure IaC）
- **特徴:** Azure OpenAIを使わず、LLMをAzure上に自前でデプロイする構成

> **TODO:** 対応LLMモデルを調査する（国内LLM試験導入との関連を確認）

### 3. Google Cloud: Lawsy（法制度AIアプリ）

- **パス:** `google-cloud/lawsy-custom-bq/`
- **用途:** 最新の法律条文データを参照・回答する法制度AIアプリの実装
- **技術:** Python / Terraform / BigQuery
- **特徴:** BigQueryに法令データを格納し、RAGで参照する構成。最も実装が充実している

> **TODO:** BigQueryのスキーマ・法令データの取得方法を確認する

---

## マイクロサービスとしての設計思想

源内WebとのプロトコルさえGUI登録すれば、独立した環境でAIアプリを構築・追加できる。つまり：

- 源内Webとは**疎結合**
- クラウドを選ばない（AWS / Azure / GCP 全対応）
- **自作AIアプリを源内に追加できる**

これがカスタマイズの最大のポイント。

---

## ライセンス

- ソフトウェア: MIT License
- ドキュメント: CC BY 4.0

---

## フォーク時の注意点

- PRは受け付けていない（公式方針）
- Issueは致命的バグのみ受付
- `mise.toml` でNode/Pythonのバージョンが固定されているため、環境構築時はmiseを使うのが推奨

---

## 調査が必要な項目

> **TODO:** 各アプリのREADMEを詳細調査する
> **TODO:** Lawsyの法令データ取得・更新フローを確認する
> **TODO:** Query Expansion RAGの使用モデルとパラメータを確認する
> **TODO:** 源内WebとのAPIプロトコル仕様を調査する（AIアプリAPI仕様.md参照）
> **TODO:** miseのインストール・バージョン設定手順を確認する
