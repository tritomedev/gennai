# genai-web 最小コスト構成パラメータ設計（デプロイ用）

- **作成日:** 2026-07-08
- **ステータス:** 設計確定 / clone後に配置予定
- **根拠:** 公式 `packages/cdk/lib/stack-input.ts`（全パラメータ定義）と `self-hosting-template.ts` を精査
- **関連:** [genai-web-aws-requirements.md](./genai-web-aws-requirements.md) / [aws-cost-guardrails.md](./aws-cost-guardrails.md)

---

## コスト事故ゼロの根拠（パラメータ全精査の結論）

`stack-input.ts` 全文検索の結果、**高額固定費リソースのパラメータは存在しない**ことを確定：

| 懸念 | 結果 |
|---|---|
| RAG / Kendra（≈¥12万/月） | **パラメータ自体が存在しない**（源内はRAGをExApp側で行う思想） |
| OpenSearch / Aurora / Vector | 同上・存在しない |
| SageMakerエンドポイント | `endpointNames` デフォルト空 → 使わない限りゼロ |
| Bedrock Guardrail | `guardrailEnabled` デフォルト false・従量課金型 |
| CloudWatchダッシュボード | `dashboard` デフォルト false（1個¥450/月を回避可） |

### 唯一の要確認：ExApp呼び出しLambdaのVPC/NAT → **synthでNAT×2を検出**

- `vpcIdForInvokeExApp` デフォルト `''`（空）→ スタックが自前VPCを作り **NAT Gateway×2＋VPCエンドポイント** を生成
- `cdk synth` 実測の結果、**NAT Gateway 2個（月約¥13,500）＋インターフェースエンドポイント（月約¥3,000）** を確認
- **これが源内Web固定費のほぼ全て**（詳細内訳・対策A/B/Cは [genai-web-aws-cost-breakdown.md](./genai-web-aws-cost-breakdown.md) 参照）
- 対策方針が決まるまでデプロイは保留（NAT対策A/B/Cの選択待ち）

---

## 確定した設計判断

| 項目 | 決定 | 理由 |
|---|---|---|
| アクセス制限（WAF） | **なし**（`allowedIpV4AddressRanges: null`） | WAF固定費ゼロ。ログインはCognitoが保護。検証段階なら十分 |
| モデル構成 | **最安**（nova-lite + claude-haiku） | Bedrockトークン代を最小化。sonnet/opusは後から追加可 |
| デフォルトモデル | claude-haiku | 安いモデルを既定に |
| SageMaker | 使わない（`endpointNames: []`） | 常時課金回避 |
| ダッシュボード | OFF（`dashboard: false`） | ¥450/月回避 |
| DB削除ポリシー | `DESTROY` | destroyで掃除しやすい |
| カスタムドメイン | なし | CloudFrontデフォルトURLで済む（Route53/ACM不要） |

---

## 配置するパラメータファイル（clone後）

`packages/cdk/env-parameters/self-hosting-dev.ts` として配置：

```typescript
import { StackInput } from '../lib/stack-input';

export const selfHostingDevParams: Partial<StackInput> = {
  appEnv: 'dev',
  logLevel: 'INFO',

  // --- 認証: 管理者がユーザー発行（セルフサインアップ無効）---
  selfSignUpEnabled: false,
  samlAuthEnabled: false,

  // --- アクセス制限: なし（最安・WAF固定費ゼロ / ログインはCognitoが保護）---
  allowedIpV4AddressRanges: null,
  allowedIpV6AddressRanges: null,

  // --- モデル: 検証用に最安構成（nova + haiku）---
  modelRegion: 'ap-northeast-1',
  modelIds: [
    'amazon.nova-lite-v1:0',
    'jp.anthropic.claude-haiku-4-5-20251001-v1:0',
  ],
  defaultModelId: 'jp.anthropic.claude-haiku-4-5-20251001-v1:0',
  imageGenerationModelIds: ['amazon.nova-canvas-v1:0'], // 使った分だけ課金。不要ならhiddenUseCasesで非表示

  // --- 常時課金の芽を摘む ---
  endpointNames: [],          // SageMakerエンドポイント無し
  guardrailEnabled: false,    // Guardrail無し
  dashboard: false,           // CloudWatchダッシュボード無し

  // --- 掃除しやすく ---
  databaseRemovalPolicy: 'DESTROY',

  // --- ExApp呼び出しVPC: 空。synthでNAT有無を確認してから最終判断 ---
  vpcIdForInvokeExApp: '',

  // --- 監視は基本のみ維持（ほぼ無料）---
  monitoring: true,
};
```

配置後、`packages/cdk/parameter.ts` の `deploy_envs` に登録：

```typescript
import { selfHostingDevParams } from './env-parameters/self-hosting-dev';

const deploy_envs: Record<string, Partial<StackInput>> = {
  '-selfHostingDev': selfHostingDevParams,
};
```

> ⚠️ **タグ付けを入れる場合**（[aws-cost-guardrails.md](./aws-cost-guardrails.md) 参照）は、CDKエントリポイントに `Tags.of(app).add('Project','genai')` を追加する。

---

## デプロイ前の最終チェック（この順で）

1. [ ] Budgetsアラート（¥3,000）設定済み
2. [ ] `cdk synth` で **NatGatewayが出ないこと**を確認（出たら `vpcIdForInvokeExApp` に既存VPC指定を検討）
3. [ ] `modelIds` が nova+haiku のみ
4. [ ] `endpointNames: []` / `dashboard: false` / `guardrailEnabled: false`
5. [ ] `cdk deploy --all -c env=-selfHostingDev`
