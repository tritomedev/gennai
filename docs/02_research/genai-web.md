# genai-web 調査ログ

- **調査日:** 2026-07-08
- **対象リポジトリ:** https://github.com/digital-go-jp/genai-web
- **最新リリース:** v1.0.3（2026年4月24日）
- **ステータス:** 調査完了（2026-07 AWS実デプロイまで実施）

---

## リポジトリ概要

源内のWebフロントエンド。AWS OSS「Generative AI Use Cases（GenU）」をベースに、行政向けの機能追加・デザイン変更を加えたもの。

**言語構成:** TypeScript 99.1% / その他 0.9%

---

## 主要ドキュメント（公式）

公式リポジトリの `docs/` に以下が整備されている：

### セットアップ系
- 事前準備.md
- デプロイ手順.md
- アカウント登録.md
- システム管理者設定手順.md
- 共通アプリチームの登録.md

### AIアプリ系
- AIアプリの種類.md
- AIアプリ登録手順書.md
- AIアプリ開発ガイド.md
- AIアプリAPI仕様.md

### 運用系
- ログ設定.md
- CI-CD設定.md
- カスタムドメイン設定.md

### 認証
- SAML認証手順.md

### 開発
- ローカル開発環境.md

---

## GenUからの主な変更点

| 項目 | 内容 |
|---|---|
| チーム管理機能 | 省庁・チーム単位のアクセス制御 |
| AIアプリ管理機能 | GUIでAIアプリの追加・管理 |
| 外部マイクロサービス連携 | 独立AIアプリをAPI経由で呼び出す仕組み |
| デザイン | デジタル庁デザインシステム適用 |
| アクセシビリティ | JIS X 8341-3:2016 AA相当の試験実施済み |
| 運用機能 | 監視・モニタリング追加 |

※ GenUとは独立して開発されており、機能構成が異なる点に注意。

---

## ライセンス注意事項

- 基本：MIT License
- 一部のLambda・CDKファイルはAWS Prototyping Programによって作成されており**Amazon Software License（ASL）**の対象
- ASL対象ファイルは `docs/ASL対象ファイル.md` に一覧あり

> **TODO:** ASL対象ファイルの一覧を確認・記録する（フォーク時の注意事項として）

---

## フォーク時の注意点

- PRは受け付けていない（公式方針）→ forkして独自に管理するのが基本
- Issueは致命的バグのみ受付
- upstreamの追従は手動で行う必要あり

---

## 調査が必要な項目

> ~~**TODO:** `packages/` 以下のディレクトリ構成を調査する~~ → ✅完了（cdk/web等のモノレポ構成を確認。[../03_setup/genai-web-aws-requirements.md](../03_setup/genai-web-aws-requirements.md)）
> ~~**TODO:** ローカル開発環境の手順を確認してdocs/03_setup/に記録する~~ → ✅完了（[../03_setup/genai-web-aws-requirements.md](../03_setup/genai-web-aws-requirements.md)。ローカルフロント起動もAWSデプロイ前提と判明）
> ~~**TODO:** デプロイ手順を確認してVPS環境での差分を整理する~~ → ✅完了（AWS実デプロイ実施。[../04_build/genai-web-deploy-record.md](../04_build/genai-web-deploy-record.md)。VPS完結は本体では不可＝ExApp側の話）
> ~~**TODO:** AIアプリAPI仕様の詳細を確認する~~ → ✅完了（[../02_research/ai-app-api-spec.md](./ai-app-api-spec.md)）
> **TODO:** ASL対象ファイルの確認
