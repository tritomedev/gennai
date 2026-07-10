# 源内 アーキテクチャ概要

- **調査日:** 2026-07-08
- **ステータス:** 調査完了（実デプロイ反映）

---

## 全体アーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│                   利用者（政府職員）                    │
└───────────────────────┬─────────────────────────────┘
                        │ SAML SSO（GSS経由）
                        ▼
┌─────────────────────────────────────────────────────┐
│                    源内 Web                          │
│  React + TypeScript / AWS CDK / Lambda / Cognito    │
│                                                     │
│  ┌────────────────┐  ┌──────────────────────────┐  │
│  │   汎用AIアプリ  │  │   行政実務用AIアプリ管理   │  │
│  │  チャット/翻訳  │  │   （GUI登録・実行）        │  │
│  └────────────────┘  └──────────┬───────────────┘  │
└─────────────────────────────────┼───────────────────┘
                                  │ API呼び出し
                                  ▼
┌─────────────────────────────────────────────────────┐
│             行政実務用AIアプリ（マイクロサービス）       │
│                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐ │
│  │  Azure上のAP │ │  GCP上のAP   │ │  AWS上のAP  │ │
│  │  LLMテンプレ │ │  Lawsy(RAG)  │ │  RAGテンプレ│ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬──────┘ │
└─────────┼────────────────┼────────────────┼─────────┘
          │                │                │
          ▼                ▼                ▼
┌──────────────────────────────────────────────────────┐
│                      LLM層                            │
│  ▼源内Web内蔵チャット = Amazon Bedrock（Claude/Nova）で確定 │
│  ▼各ExAppは各自別途調達（Azure OpenAI / Vertex AI / 自前等）│
│  ＋ 国内LLM（2026年夏〜試験導入予定）                   │
└──────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────┐
│                  データソース層                        │
│  法令データ / 官報 / 各省庁ナレッジベース               │
└──────────────────────────────────────────────────────┘
```

---

## genai-web の内部構成

```
genai-web/
├── packages/         # モノレポ構成
├── docs/             # セットアップ・運用ドキュメント
│   ├── 事前準備.md
│   ├── デプロイ手順.md
│   ├── アーキテクチャ.md
│   ├── AIアプリの種類.md
│   ├── AIアプリ開発ガイド.md
│   └── AIアプリAPI仕様.md
└── scripts/
```

> ~~**TODO:** `packages/` 以下の詳細構成を調査する~~ → ✅完了（cdk/web等のモノレポ構成を確認。[../03_setup/genai-web-aws-requirements.md](../03_setup/genai-web-aws-requirements.md)）

---

## genai-ai-api の内部構成

```
genai-ai-api/
├── aws/
│   └── query-expansion-rag/     # RAG開発テンプレート（AWS）
├── azure/
│   └── genai-azure/             # LLMセルフデプロイテンプレート（Azure）
├── google-cloud/
│   └── lawsy-custom-bq/         # 法令RAGアプリ（GCP）
├── .vscode/
├── biome.json                   # リンター設定
├── mise.toml                    # ツールバージョン管理
└── pyproject.toml               # Python設定
```

---

## AIアプリのプロトコル

源内WebとAIアプリはAPIで連携する。プロトコルに準拠すれば独立した環境でAIアプリを構築・追加できる。

詳細は公式ドキュメント参照:
- [AIアプリの種類](https://github.com/digital-go-jp/genai-web/blob/main/docs/AI%E3%82%A2%E3%83%97%E3%83%AA%E3%81%AE%E7%A8%AE%E9%A1%9E.md)
- [AIアプリ開発ガイド](https://github.com/digital-go-jp/genai-web/blob/main/docs/AI%E3%82%A2%E3%83%97%E3%83%AA%E9%96%8B%E7%99%BA%E3%82%AC%E3%82%A4%E3%83%89.md)
- [AIアプリAPI仕様](https://github.com/digital-go-jp/genai-web/blob/main/docs/AI%E3%82%A2%E3%83%97%E3%83%AAAPI%E4%BB%95%E6%A7%98.md)

> ~~**TODO:** API仕様の詳細を調査してまとめる~~ → ✅完了（[../02_research/ai-app-api-spec.md](../02_research/ai-app-api-spec.md)）

---

## 技術スタック一覧

| コンポーネント | 技術 |
|---|---|
| フロントエンド | React / TypeScript / Tailwind CSS |
| インフラ（IaC） | AWS CDK / Bicep（Azure）/ Terraform（GCP） |
| バックエンド | AWS Lambda |
| 認証 | AWS Cognito / SAML |
| AIアプリ（Python系） | Python / FastAPI系 |
| AIアプリ（TS系） | TypeScript / Node.js |
| コード品質 | Biome（Linter/Formatter） |
| バージョン管理 | mise（Node/Python バージョン統一） |

---

## 調査が必要な項目

> ~~**TODO:** genai-webのpackages/以下の詳細構成を確認する~~ → ✅完了（[../03_setup/genai-web-aws-requirements.md](../03_setup/genai-web-aws-requirements.md)）
> ~~**TODO:** AIアプリAPI仕様（リクエスト/レスポンス形式）を調査する~~ → ✅完了（[../02_research/ai-app-api-spec.md](../02_research/ai-app-api-spec.md)）
> **TODO:** Cognito → SAML連携の具体的な設定を確認する
> **TODO:** GenUとの差分を整理する
