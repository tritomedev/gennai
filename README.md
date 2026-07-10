# gennai - ガバメントAI「源内」研究・検証リポジトリ

> デジタル庁が開発・公開するOSS「源内（GenAI）」の調査・ビルド・カスタマイズ・サービス展開検討を行うリポジトリです。

## 📌 このリポジトリについて

本リポジトリは、デジタル庁が開発・運用する政府職員向け生成AI利用環境「源内」を独自に研究・検証し、源内を活用したサービス展開のアプローチを探ることを目的としています。

得られた知見はドキュメントとして蓄積し、同じく源内に取り組む方々との情報共有を意識して整備しています。

> 🚀 **はじめて読む方へ →** [docs/01_overview/START-HERE.md](./docs/01_overview/START-HERE.md)（源内とは・全体構成・現状・狙いを1枚で）

**現状（2026-07）:** 源内WebをAWS（東京）に実デプロイして稼働確認、自作ExApp（echo-observer）を登録して源内の実挙動まで観察済み。詳細は [docs/04_build/](./docs/04_build/)。

## 🗂️ ドキュメント構成

| ディレクトリ | 内容 |
|---|---|
| [docs/01_overview](./docs/01_overview/) | 源内とは何か（調査・解析結果） |
| [docs/02_research](./docs/02_research/) | 技術調査ログ |
| [docs/03_setup](./docs/03_setup/) | 環境構築手順 |
| [docs/04_build](./docs/04_build/) | ビルド・デプロイ記録 |
| [docs/05_customization](./docs/05_customization/) | カスタマイズ・サービス展開検討 |
| [docs/06_knowledge](./docs/06_knowledge/) | 知見・TIL・トラブルシュート |

## 🔗 関連リポジトリ（フォーク元）

源内の公式OSSリポジトリは以下の2つで構成されています。

| リポジトリ | 概要 | 言語 |
|---|---|---|
| [digital-go-jp/genai-web](https://github.com/digital-go-jp/genai-web) | 源内Webフロントエンド（AIインターフェース） | TypeScript / AWS CDK |
| [digital-go-jp/genai-ai-api](https://github.com/digital-go-jp/genai-ai-api) | 行政実務用AIアプリ群（マイクロサービス） | Python / TypeScript / Terraform |

> **フォーク運用方針：** 本リポジトリでは上記2リポジトリをフォークし、独自の検証・カスタマイズを行います。詳細は [CONTRIBUTING.md](./CONTRIBUTING.md) を参照してください。

## 🏛️ 源内とは

デジタル庁が開発・運用する生成AI利用環境。2026年度中に全府省庁約18万人の政府職員への展開を目指す国産ガバメントAIプラットフォームで、2026年4月にMITライセンスでOSSとして公開されました。

**重要な性質：源内はAIそのものではなく「指揮者（オーケストレーター）」です。** LLMも業務知識も持たず、内蔵チャットはLLM（Amazon Bedrock）を、業務アプリはExApp（外部AIアプリ）を呼び出して束ねます。組織固有の賢い処理は全てExApp側が担います。

詳細 → [docs/01_overview/START-HERE.md](./docs/01_overview/START-HERE.md) / [docs/01_overview/what-is-gennai.md](./docs/01_overview/what-is-gennai.md)

## 📚 参考リンク

- [デジタル庁 ガバメントAI「源内」公式ページ](https://www.digital.go.jp/policies/genai)
- [デジタル庁 TechブログNote](https://digital-gov.note.jp/m/m90208c3610d0)

## 📝 ドキュメントへの追記ルール

→ [CONTRIBUTING.md](./CONTRIBUTING.md) を参照してください。
