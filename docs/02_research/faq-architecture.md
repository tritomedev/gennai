# 源内 アーキテクチャ・環境 FAQ

- **調査日:** 2026-07-08
- **ステータス:** 完了

---

## Q. ローカルで動かせるの？

**半分YES・半分NO。**

ローカル開発環境は起動できて `http://localhost:5173/` でフロントのUIは動く。ただし前提条件として「デプロイ手順に従ってAWS環境が構築済みであること」が必要。

つまり**UIの開発・確認はローカルでできるけど、バックエンド（Lambda・Cognito・Bedrock等）はAWSが必要**。完全ローカル完結は無理。

```sh
# ローカル起動コマンド
sh scripts/run.sh 環境名（例: -dev）

# 成功すると以下が出力される
# ➜  Local:   http://localhost:5173/
```

> **補足:** `packages/web/` 以下の変更は即時反映されるが、`packages/cdk/` 以下の変更は再デプロイが必要。

---

## Q. サーバーどのくらいの規模が必要？

**自前サーバーは不要。AWSのサーバーレス構成がベース。**

genai-webのデプロイはAWS CDKで行う。必要なものはAWSアカウントとローカルのツール類のみ。

### 必要ツール（ローカル）

| ツール | 用途 |
|---|---|
| Node.js | ビルド・CDK実行 |
| AWS CLI | AWSアカウント操作 |
| AWS CDK CLI | インフラデプロイ |
| jq | JSONパース |
| mise（任意） | Node/Pythonバージョン管理 |

### AWSで使われるサービス（推定）

- **CloudFront** → フロント配信
- **Lambda** → バックエンド処理
- **Cognito** → 認証
- **Bedrock** → LLM呼び出し
- **S3** → 静的ファイル等

### セルフホスティング構成について

セルフホスティング用のパラメータテンプレート（`self-hosting-template.ts`）が用意されており、環境ごとの設定ファイルを作ってデプロイする構成になっている。

```sh
# セルフホスティング用パラメータファイルの準備
cd packages/cdk/env-parameters
cp self-hosting-template.ts self-hosting-dev.ts

# デプロイ
npm -w packages/cdk run cdk -- deploy --all --require-approval never -c env=-selfHostingDev
```

> **⚠️ VPS環境への注意:** genai-webはAWS前提の設計のため、VPSに直接移植するのはコストが高い。現実的なアプローチは後述。

---

## Q. genai-webとgenai-ai-apiの住み分けは？

```
genai-web（源内Web）
  → ユーザーが触るUI全般
  → チャット・翻訳・要約などの汎用AI機能
  → AIアプリの管理画面（追加・削除・GUI登録）
  → AWSに丸ごとデプロイ

genai-ai-api（AIアプリ群）
  → 行政実務特化のAIアプリ（RAG・法令検索等）
  → 源内WebからAPI経由で呼ばれるマイクロサービス
  → AWS / Azure / GCP それぞれに独立してデプロイ可能
  → 源内Webと疎結合（プロトコル準拠すれば自作も追加できる）
```

**重要ポイント:** 源内WebはAIインターフェースとして機能し、genai-ai-apiで管理するAIアプリとAPI連携する設計。AIアプリはGUIで登録するだけで源内Webに追加できる。

---

## Q. 源内は何が得意？

| 得意なこと | 苦手・難しいこと |
|---|---|
| チャット・翻訳・要約（汎用AI） | AWS以外へのフルデプロイ |
| 行政文書RAG（法令・官報等） | 完全ローカル動作 |
| 独自AIアプリの追加（プロトコル準拠） | LLM自体のホスティング（外部LLM前提）|
| チーム・権限管理 | |
| SAML認証（SSO連携） | |

---

## Q. VPS環境でどう活かすか？

genai-webをそのままVPSに移植するのはAWS依存が強くコストが高い。現実的なアプローチは以下の3つ。

| アプローチ | 内容 | 難易度 |
|---|---|---|
| **A: AIアプリ単体をVPSで動かす** | genai-ai-api（Lawsy・RAG等）をVPS上のコンテナで動かす | ★★☆ |
| **B: WebはAWS・AIアプリはVPS** | genai-webはAWS上、VPSはAIアプリのホスティングに使う | ★★☆ |
| **C: 源内プロトコル準拠の自作アプリ** | プロトコルに準拠した独自AIアプリを自作してVPSで動かす | ★★★ |

> **TODO:** 各アプローチの詳細な実現可能性調査 → `docs/05_customization/deployment-approaches.md` に追記予定

---

## 参考リンク

- [事前準備.md（公式）](https://github.com/digital-go-jp/genai-web/blob/main/docs/%E4%BA%8B%E5%89%8D%E6%BA%96%E5%82%99.md)
- [デプロイ手順.md（公式）](https://github.com/digital-go-jp/genai-web/blob/main/docs/%E3%83%87%E3%83%97%E3%83%AD%E3%82%A4%E6%89%8B%E9%A0%86.md)
- [ローカル開発環境.md（公式）](https://github.com/digital-go-jp/genai-web/blob/main/docs/%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83.md)
- [アーキテクチャ.md（公式）](https://github.com/digital-go-jp/genai-web/blob/main/docs/%E3%82%A2%E3%83%BC%E3%82%AD%E3%83%86%E3%82%AF%E3%83%81%E3%83%A3.md)
