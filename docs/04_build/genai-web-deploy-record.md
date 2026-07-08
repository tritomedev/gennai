# genai-web AWSデプロイ記録（TASK-029）

- **デプロイ日:** 2026-07-08
- **ステータス:** デプロイ成功・稼働中
- **アカウント:** 704983044653 / リージョン ap-northeast-1（東京）
- **フォーク:** tsucha-nsdq/genai-web ブランチ `feature/poc-minimal-cost-vpc-disabled`

---

## アクセス情報

| 項目 | 値 |
|---|---|
| **源内Web URL** | https://drx8ehrhmih8b.cloudfront.net |
| UserPool ID | ap-northeast-1_OoPyNFI4s |
| ApiEndpoint | https://pt1aklbvhl.execute-api.ap-northeast-1.amazonaws.com/api/ |
| モデル | amazon.nova-lite-v1:0 / jp.anthropic.claude-haiku-4-5 |
| 初期管理者 | daisuke.noda@nowroading.com（UserGroup + SystemAdminGroup） |

---

## デプロイまでの手順（実施済み）

1. Node 22.22.2 導入（nodenvのnode-build定義を手動追加）
2. `tsucha-nsdq/genai-web` をフォーク&clone、`npm ci`
3. 最小コスト構成パラメータ配置（[genai-web-minimal-param-design.md](../03_setup/genai-web-minimal-param-design.md)）
4. `cdk bootstrap`（ap-northeast-1 + us-east-1）
5. `cdk deploy --all -c env=-selfHostingDev`
6. Cognitoに管理者ユーザー作成 + SystemAdminGroup付与

---

## 遭遇した問題と対処（POC限定の改変2点）

### 1. ExApp用VPC/NATによる固定費（¥17,000/月）

- 原因: ExApp呼び出しLambdaがVPC内に配置され、NAT Gateway×2等が生成される
- 対処: `vpcIdForInvokeExApp: 'DISABLED'` 分岐を追加しVPCごと撤廃 → 固定費¥600/月
- 詳細: [genai-web-aws-cost-breakdown.md](../03_setup/genai-web-aws-cost-breakdown.md)

### 2. Lambdaメモリ512MB上限エラー（新規アカウント制限）

- 症状: `'MemorySize' value failed to satisfy constraint: Member must have value less than or equal to 512`
- 原因: 新規AWSアカウントはLambdaメモリが512MBに制限される（不正対策）。源内には1024MB指定のLambdaが12個あり抵触
- 対処: CDK Aspect（`bin/generative-ai-use-cases.ts` の `CapLambdaMemoryAspect`）で全Lambdaのメモリを512MBにキャップ
- 正攻法: AWSサポートに512制限の解除を申請 → 解除後はAspectを外す（本番向け）

> **いずれもPOC限定の割り切り。本番移行時は両方戻すこと。**

---

## デプロイ後の初期設定

`selfSignUpEnabled: false` のため管理者が手動でユーザー発行する運用：

```bash
POOL=ap-northeast-1_OoPyNFI4s
# ユーザー作成（招待メール送信）
aws cognito-idp admin-create-user --user-pool-id $POOL --username <email> \
  --user-attributes Name=email,Value=<email> Name=email_verified,Value=true \
  --desired-delivery-mediums EMAIL
# グループ追加
aws cognito-idp admin-add-user-to-group --user-pool-id $POOL --username <email> --group-name UserGroup
aws cognito-idp admin-add-user-to-group --user-pool-id $POOL --username <email> --group-name SystemAdminGroup
```

---

## 撤去方法（検証終了時）

```bash
cd genai-web
npm -w packages/cdk run cdk -- destroy --all -c env=-selfHostingDev
```

---

## 次のステップ

- [ ] 源内Webにログインし初期設定（チーム作成）
- [ ] echo-observer を公開ホストしてExApp登録・実リクエスト観察（TASK-002の残り）
- [ ] Anthropic利用用途フォーム提出済みか確認（Claude呼び出しに必要）
