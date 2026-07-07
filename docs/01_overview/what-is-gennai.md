# 源内（GenAI）とは

- **調査日:** 2026-07-08
- **ステータス:** 完了

---

## 概要

源内（げんない）は、デジタル庁が開発・運用する**政府職員向け生成AI利用環境**。2026年4月にMITライセンスでOSSとして公開された。

2026年度中に全府省庁約18万人の政府職員への展開を目指しており、2026年5月から大規模実証が開始されている。

参照: https://www.digital.go.jp/policies/genai

---

## システム構成

源内は大きく2つのシステムで構成される。

```
[ 利用者 ]
    ↓
[ 源内 Web ] ← フロントエンド（genai-web）
    ↓
[ 行政実務用AIアプリ群 ] ← マイクロサービス（genai-ai-api）
    ↓
[ LLM（Azure OpenAI / AWS Bedrock 等） ]
```

### 1. 源内 Web（genai-web）

- **リポジトリ:** https://github.com/digital-go-jp/genai-web
- **ベース:** AWS OSS「Generative AI Use Cases（GenU）」
- **主要技術:** TypeScript / React / Tailwind CSS / AWS CDK / AWS Lambda
- **認証:** SAML認証（省庁SSOと連携）、AWS Cognito
- **デプロイ先:** AWS（ガバメントクラウド）

GenUをベースに以下を追加・変更している：

| 追加・変更点 | 内容 |
|---|---|
| チーム管理機能 | 省庁・チーム単位でのアクセス制御 |
| AIアプリ管理機能 | GUIでAIアプリの追加・管理が可能 |
| 外部マイクロサービス実行 | 独立したAIアプリをAPIで呼び出せる |
| デザインシステム適用 | デジタル庁デザインシステムに準拠 |
| 運用機能 | 監視・モニタリング等 |

### 2. 行政実務用AIアプリ（genai-ai-api）

- **リポジトリ:** https://github.com/digital-go-jp/genai-ai-api
- **主要技術:** Python / TypeScript / Bicep / Terraform / CDK
- **設計思想:** 源内WebとのプロトコルさえGUIで登録すれば、独立した環境でAIアプリを追加できるマイクロサービス構成

クラウド別に以下のアプリが公開されている：

| クラウド | 公開内容 |
|---|---|
| **Microsoft Azure** | LLMをセルフデプロイする開発テンプレート |
| **Google Cloud** | 法令条文データを参照するRAGアプリ（Lawsy） |
| **Amazon Web Services** | Query Expansion RAG開発テンプレート |

---

## 提供AIアプリの種類

### 汎用AI
- 対話型チャット
- 文章作成・要約・校正
- 翻訳（PLaMo翻訳も統合済み）

### 行政実務用AI
- 国会答弁作成支援AI
- 法制度調査支援AI（Lawsy）
- 行政資料RAGアプリ
- バックオフィス業務支援AI

---

## 展開スケジュール

| 時期 | 内容 |
|---|---|
| 2025年5月 | デジタル庁内で運用開始 |
| 2026年1月 | 一部省庁で試験的利用（v1.0）|
| 2026年4月 | OSSとして公開 |
| 2026年5月〜 | 全府省庁への大規模実証（v2.0）|
| 2026年夏 | 国内LLMの試験導入（v2.1）|
| 2026年12月 | 高度AIアプリの試験提供（v2.2）|
| 2027年度〜 | 本格利用（v3.0）|

---

## ライセンス

- ソフトウェア: [MIT License](https://github.com/digital-go-jp/genai-web/blob/main/LICENSE)
- ドキュメント: [CC BY 4.0](https://github.com/digital-go-jp/genai-web/blob/main/LICENSE-CC-BY)

商用・改変・再配布が自由に行える。

---

## 参考リンク

- [デジタル庁 公式ページ](https://www.digital.go.jp/policies/genai)
- [デジタル庁 Techブログ](https://digital-gov.note.jp/m/m90208c3610d0)
- [ガバメントAI構想紹介（note）](https://digital-gov.note.jp/n/ndc07326b7491)
