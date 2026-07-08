# genai-web デプロイ要件・手順の洗い出し（TASK-001 事前調査）

- **調査日:** 2026-07-08
- **ステータス:** 一次情報（公式docs / cdk.json）による洗い出し完了 / 実デプロイは未実施
- **調査元（すべて公式リポジトリ直取得）:**
  - `docs/事前準備.md` / `docs/デプロイ手順.md` / `docs/ローカル開発環境.md` / `README.md`
  - `packages/cdk/cdk.json` / `.node-version` / `packages/cdk/env-parameters/self-hosting-template.ts`
- **目的:** 「源内Webをどこに立てるか」を判断するため、AWS要件・費用・手順を憶測なしで洗い出す

---

## 最重要の結論：AWSデプロイは回避不能

`docs/ローカル開発環境.md` の **前提条件** に明記：

> 前提条件：[デプロイ手順](デプロイ手順.md)に従って環境が構築済みであること。

- `sh scripts/run.sh -dev` で起動するのは **ローカルのViteフロント（localhost:5173）だけ**
- そのフロントは **デプロイ済みのAWSバックエンドに接続しに行く**
- → **「フロントだけローカルで完全スタンドアロン動作」は不可能**。AWSデプロイが全ての入口。
- これは CLAUDE.md 確定結論⑤（フロントのみローカル可・バックエンドAWS必須）の実体。

**したがって TASK-001 は実質「AWSにデプロイする」以外の選択肢がない**（VPS完結は本体では不可。VPS路線はExApp側＝別アプローチ）。

---

## AWS要件（デプロイ前提）

### 必要ツール（`事前準備.md`）

| ツール | 備考 |
|---|---|
| Node.js | **v22.22.2**（`.node-version`で確認）。mise推奨 |
| AWS CLI | 認証情報の設定が必要（＝**AWSアカウント必須**） |
| AWS CDK CLI | IaCデプロイに使用 |
| jq | 必須 |
| 依存 | `npm ci` |
| CDK Bootstrap | `npm -w packages/cdk run cdk -- bootstrap`（アカウント×リージョン初回のみ） |

### 追加の前提（`cdk.json` から判明）

- **リージョン: `ap-northeast-1`（東京）固定運用**（`modelRegion`。トラブルシュートにも「profileのリージョンをap-northeast-1に」と明記）
- **Amazon Bedrock のモデルアクセス有効化が必須**。内蔵チャットが使うモデル：
  - `jp.anthropic.claude-opus-4-8`
  - `jp.anthropic.claude-sonnet-4-6`
  - `jp.anthropic.claude-haiku-4-5-20251001-v1:0`
  - `amazon.nova-lite-v1:0`（テキスト） / `amazon.nova-canvas-v1:0`（画像生成）
  - → これらを **Bedrockコンソールで事前にアクセス申請/有効化**しておく必要がある
- 認証は **Cognito**（`selfSignUpEnabled: false` がデフォルト＝管理者がユーザー発行）

---

## デプロイ手順の要点（`デプロイ手順.md`）

```bash
# 1. パラメータファイルを用意
cd packages/cdk/env-parameters
cp self-hosting-template.ts self-hosting-dev.ts
#   → appEnv（必須）などを編集

# 2. parameter.ts の deploy_envs に登録
#    "-selfHostingDev": selfHostingDevParams,

# 3. デプロイ
npm -w packages/cdk run cdk -- deploy --all --require-approval never -c env=-selfHostingDev

# 4. 完了後、CloudFront の URL にアクセス → ログイン画面が出れば成功
```

デプロイ後は `アカウント登録.md` → `システム管理者設定手順.md` → `共通アプリチームの登録.md` の順で初期設定（未取得。デプロイ段階で読む）。

---

## リソース構成と費用の見立て

> ⚠️ ベースは AWS OSS「GenU（Generative AI Use Cases）」。リソースの詳細図は公式 `docs/drawio/genai.drawio`（画像）にあり未取得。以下の構成は **cdk.json の設定値から確実に言えるもの** と **GenUベースからの推定** を分けて記載。

### cdk.json から確実に使うと分かるもの

- **DynamoDB**（`dataRetentionDays.dynamoDbTtl: 364`）
- **S3**（`s3FileExpiration: 364`）
- **Cognito**（認証設定群）
- **WAF / IP制限**（`allowedIpV4AddressRanges` を設定した場合）
- **Amazon Bedrock**（`modelIds`。従量課金の主因）
- **ExApp呼び出しタイムアウト: 29秒**（`exAppInvokeTimeoutSeconds: 29`）← 自作AIアプリは29秒以内に同期応答必須。超えるなら非同期ポーリング

### GenUベースからの推定（要デプロイ後確認）

- CloudFront + S3 静的ホスティング（フロント）
- API Gateway + Lambda（バックエンド、サーバーレス）
- 基本サーバーレス構成のため **常時起動の高額リソース（RDS/NAT Gateway等）は基本なし**の想定

### 費用の見立て

- **アイドル時（デプロイして放置）**：ほぼ無料〜月数百円程度（S3/DynamoDB/Lambda/CloudFrontの従量課金は低額）
- **主コスト = Bedrock のトークン従量課金**（使った分だけ）。検証は **haiku / nova に絞れば激安**、opus-4-8 は単価高いので注意
- WAF を有効化すると固定費が少し乗る（IP制限を使う場合）
- カスタムドメインを使わなければ CloudFront デフォルトURLで済む（Route53不要）

> **TODO:** 実デプロイ後、AWS Cost Explorer で実額を確認して本節を更新する
> **TODO:** GenUのデプロイ済みリソース一覧を CloudFormation スタックから確認する（RDS/NAT有無の確定）

---

## ライセンス注意（フォーク時）

- 本体は **MIT**。ただし一部 Lambda/CDK は **ASL（Amazon Software License）** 対象（`docs/ASL対象ファイル.md`、未取得）
- ドキュメントは **CC BY 4.0**
- PRは受付なし・Issueは致命的バグのみ → **フォークして独自管理**が前提

---

## この調査で判明した新事実（他ドキュメントへ反映済み/予定）

1. **ExAppタイムアウト = 29秒**（`ai-app-api-spec.md` のTODO「非同期タイムアウト要確認」の回答）
2. **内蔵チャットのLLM = Amazon Bedrock（Claude opus/sonnet/haiku + Nova）**。確定結論②（内蔵チャットのLLMは自作ExAppと共有不可）と整合。ExApp側は別途LLM調達が必要という結論は不変
3. **ローカルフロント起動もAWSデプロイが前提**（完全ローカル不可の実体）

---

## 次のアクション

TASK-001 を進めるなら、前提として以下を先に潰す必要がある：

1. AWSアカウントの用意（or 既存アカウント確認）
2. **Bedrock モデルアクセス有効化**（ap-northeast-1 で上記modelIds、最低限 haiku/nova）
3. ローカルにツール群インストール（Node v22.22.2 / AWS CLI / CDK CLI / jq）
4. `cdk bootstrap` → パラメータ設定 → `cdk deploy`
