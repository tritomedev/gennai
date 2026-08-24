# AWSコスト事故防止ガードレール（デプロイ前設定）

> 環境固有の値は `<...>` のプレースホルダにしている。実値は内部管理の `private/environment.md` を参照。


- **作成日:** 2026-07-08
- **ステータス:** 手順まとめ＋**実設定済み（2026-07。Budgets設定済み・genai-web を AWS 東京へデプロイ済み。[../04_build/genai-web-deploy-record.md](../04_build/genai-web-deploy-record.md) 参照）**
- **対象:** 会社AWSアカウントで genai-web をデプロイする前に入れておく安全策
- **目的:** 想定外課金の事故を防ぐ。特に RAG系（Kendra/OpenSearch）の高額固定費と、Bedrock 使いすぎを早期検知する

---

## 前提：源内Webの費用構造（おさらい）

- 固定費：ほぼ¥0〜¥1,500/月（GenUベースでサーバーレス中心）
- 従量：主に **Bedrock のトークン代**（haiku/nova中心なら検証で月¥数百）
- **地雷**：RAG系オプション（Kendra ≈¥12万/月、OpenSearch Serverless ≈¥5万/月〜）を有効化しないこと
  - ※**注記:** 源内コア（genai-web）には Kendra/OpenSearch のパラメータ自体が存在しないため、源内本体ではこれらの費用は発生しない。RAG は ExApp 側の責務であり、ExApp 側で自前にそうした基盤を足す場合の一般的注意として読むこと
- 詳細: [genai-web-aws-requirements.md](./genai-web-aws-requirements.md)

---

## 1. AWS Budgets アラート（月¥3,000で通知）

「予算額を超えそう／超えた」ときにメール通知する仕組み。デプロイ前に必ず入れる。

### コンソール手順（日本語UI）

1. AWSコンソール右上のアカウント名 → **「請求とコスト管理（Billing and Cost Management）」**
2. 左メニュー **「予算（Budgets）」** → **「予算を作成」**
3. **「テンプレートを使用（推奨）」** → **「月次コスト予算」** を選択
4. 設定：
   - **予算名**: `genai-monthly-3000jpy` など
   - **予算額**: `3000`（通貨はアカウントの請求通貨。USD建てなら約 `20` USD ≈ ¥3,000 で設定）
   - **メール受信者**: 通知を受け取るメールアドレス
5. 既定で **実績が予算の85%/100%** と **予測が100%** に達した時に通知される。しきい値は編集可能
   - おすすめ追加：**予測が80%（¥2,400）で早期通知**を1本足すと、月末を待たず異常に気づける
6. 「予算を作成」で完了

### CLI（AWS CLI導入後に使う場合）

```bash
# budget.json と notifications.json を用意して実行
aws budgets create-budget \
  --account-id <YOUR_ACCOUNT_ID> \
  --budget file://budget.json \
  --notifications-with-subscribers file://notifications.json
```

`budget.json`（例）:
```json
{
  "BudgetName": "genai-monthly-3000jpy",
  "BudgetLimit": { "Amount": "3000", "Unit": "JPY" },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
```

> **Note（2026-08-24 実測で判明）:** CLI の `create-budget` では **`JPY` は指定できない**。
> `InvalidParameterException: JPY is not in the supported unit set: [USD]` になる。
> **USD建てで指定すること**（¥3,000相当なら `"Amount": "20", "Unit": "USD"`）。
> 新アカウント <AWS_ACCOUNT_ID> では `gennai-monthly-20usd`（実績50% / 実績100% / 予測100% の3通知）を設定済み。

---

## 2. コストタグ付け（請求を genai 単位で見える化）

### 重要な訂正：リソース名プレフィックスだけでは請求フィルタできない

`appEnv`（例 `dev`）は**リソース名のプレフィックス**になるが、これは名前での識別用。
**請求（Cost Explorer）でフィルタするにはリソースに「タグ」を付け、それを「コスト配分タグ」として有効化**する必要がある。

### やり方：CDKで全リソースに一括タグ付け

デプロイ前に、CDKのエントリポイント（`packages/cdk/bin/generative-ai-use-cases.ts` 付近）で全体にタグを付ける：

```typescript
import { Tags } from 'aws-cdk-lib';
// app 定義の後で
Tags.of(app).add('Project', 'genai');
Tags.of(app).add('Env', 'dev');
```

> フォーク運用なので、この変更は自分たちのフォークに入れて管理する（upstreamはPR不可）。

### コスト配分タグの有効化

1. 「請求とコスト管理」→ 左メニュー **「コスト配分タグ」**
2. **ユーザー定義のコスト配分タグ** の一覧から `Project` / `Env` を選び **「有効化」**
3. 反映は**約24時間後、かつ有効化以降に発生したコストのみ**対象（過去分は遡及されない）

### 請求の確認（Cost Explorer）

- 「Cost Explorer」→ フィルタ/グループ化で **タグ `Project=genai`** を指定 → genai関連のコストだけ抽出できる

> **補足:** タグ付けをしない場合でも、Cost Explorer の「サービス別」グループ化で Bedrock / CloudFront 等の内訳は見られる。genai専用アカウントに近い使い方なら、まずはサービス別だけでも十分。

---

## 3. 撤去（cdk destroy）

検証が終わったら、または作り直したいときにスタックを削除する。

```bash
npm -w packages/cdk run cdk -- destroy --all -c env=-selfHostingDev
```

### 注意点

- **消えないリソースがある**：`RemovalPolicy.RETAIN` が付いた S3バケット・DynamoDB・Cognito等は destroy 後も残ることがある。残ったものはコンソールから手動削除
- **中身が入ったS3バケット**は削除に失敗することがある（先に空にする必要あり）
- destroy してもBudgets/コスト配分タグの設定は残る（アカウント単位の設定のため）
- サーバーレス構成なので「放置」でも固定費は小さいが、会社アカウントはキレイに撤去しておくのが無難

---

## デプロイ前チェックリスト

- [ ] Budgets アラート（¥3,000）を設定した
- [ ] CDKに `Tags.of(app).add('Project','genai')` を入れた（任意だが推奨）
- [ ] **RAG系（Kendra/OpenSearch）フラグがOFF**であることをパラメータで確認した ← 最重要
- [ ] `modelIds` を検証用に haiku/nova 中心へ絞る設計にした（次ステップで実施）
