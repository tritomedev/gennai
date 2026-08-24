# genai-web AWSデプロイ記録（TASK-029）

> 環境固有の値は `<...>` のプレースホルダにしている。実値は内部管理の `private/environment.md` を参照。


- **デプロイ日:** 2026-07-08（旧アカウント）／ 2026-08-22（新アカウントへ移行）
- **ステータス:** デプロイ成功・稼働中
- **アカウント:** <OLD_AWS_ACCOUNT_ID> / リージョン ap-northeast-1（東京）
- **フォーク:** tsucha-nsdq/genai-web ブランチ `feature/poc-minimal-cost-vpc-disabled`

---

## アクセス情報

| 項目 | 値 |
|---|---|
| **源内Web URL** | <OLD_CLOUDFRONT_URL> |
| UserPool ID | <OLD_USER_POOL_ID> |
| ApiEndpoint | <OLD_API_ENDPOINT> |
| モデル | amazon.nova-lite-v1:0 / jp.anthropic.claude-haiku-4-5 |
| 初期管理者 | <ADMIN_EMAIL>（UserGroup + SystemAdminGroup） |

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
POOL=<OLD_USER_POOL_ID>
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


---

# 新アカウントへの移行（TASK-042 / 2026-08-22）

- **アカウント:** <AWS_ACCOUNT_ID> / ap-northeast-1（IAM: user/noda、CLIプロファイル `gennai-prod`）
- **ブランチ:** `feature/poc-minimal-cost-vpc-disabled`（旧アカウントと同一。パラメータも `-selfHostingDev` を流用）

## アクセス情報（新）

| 項目 | 値 |
|---|---|
| **源内Web URL** | https://tritome-gennai-sample.com |
| UserPool ID | <USER_POOL_ID> |
| UserPoolClient ID | <USER_POOL_CLIENT_ID> |
| IdPool ID | <IDENTITY_POOL_ID> |
| TeamAccessControl API | <TEAM_ACCESS_CONTROL_API> |
| モデル | nova-lite / claude-haiku-4-5 / claude-sonnet-4-6（既定=haiku-4-5） |

## 手順（実施済み）

```bash
cd genai-web
npm -w packages/cdk run cdk -- bootstrap aws://<AWS_ACCOUNT_ID>/ap-northeast-1 --profile gennai-prod
npm -w packages/cdk run cdk -- bootstrap aws://<AWS_ACCOUNT_ID>/us-east-1     --profile gennai-prod
npm -w packages/cdk run cdk -- synth  -c env=-selfHostingDev --profile gennai-prod
npm -w packages/cdk run cdk -- deploy --all --require-approval never -c env=-selfHostingDev --profile gennai-prod
```

- **所要時間: 499秒（約8分20秒）**。ap-northeast-1 の bootstrap は ExApp スタック用に実施済みだったため、
  今回追加で必要だったのは **us-east-1 の bootstrap**（CloudFront/WAF用）のみ。
- デプロイ後の確認：CloudFront **200**／**NAT Gateway 0件**／**既定以外のVPC 0件**（固定費の地雷なし）。

## 詰まったこと：cdk.out に残る古いテンプレートで誤判断しかけた

デプロイ前の `synth` 確認で `packages/cdk/cdk.out/*.template.json` を grep したところ
**NAT Gateway が2件検出され**、VPC撤廃の改変が壊れたかと調査に入った。実際は：

- `bootstrap` 実行時にも synth が走るが、その際は `-c env=-selfHostingDev` が付かないため
  `vpcIdForInvokeExApp` が既定値 `''` になり、**VPCを新規作成する構成のテンプレートが生成される**。
- CDK は `cdk.out` を消さずに書き足すため、**env未指定時の残骸ファイルが残り続ける**。
  ネストスタックのファイル名はハッシュ付き（`...TeamAccessControlStackA1BAF48A.nested.template.json` と
  `...selfHostingDevTeamAccessControlStack7898EB1E.nested.template.json`）なので別ファイルとして共存する。
- `rm -rf packages/cdk/cdk.out` してから synth し直すと NAT/VPC ともに **0件**。改変は正常に機能していた。

**教訓: `cdk.out` をワイルドカードで検査するときは、事前にディレクトリを消すか、
対象スタックのテンプレートをファイル名で特定すること。**

なお切り分けの過程で、`parameter.ts` と `construct/team-access-control.ts` に一時的な
`console.error` を入れて実値を確認した（いずれも `vpcIdForInvokeExApp="DISABLED"` が
construct まで正しく届いていることを確認済み。コードは `git checkout` で復元済み）。

## 独自ドメインの設定（2026-08-24 / TASK-047）

| 項目 | 値 |
|---|---|
| ドメイン | `tritome-gennai-sample.com`（Route 53・自動更新ON） |
| ホストゾーンID | `<HOSTED_ZONE_ID>`（ドメイン取得時に自動作成） |
| 証明書 | ACM（us-east-1）／SANに `www.` ／有効期限 2027-03-09・自動更新 |

```bash
# パラメータを設定して deploy するだけ（証明書の発行・DNS検証・CloudFront紐付けは全自動）
npm -w packages/cdk run cdk -- deploy --all --require-approval never \
  -c env=-selfHostingDev --profile gennai-prod
```

所要時間：AppDomainStack **170秒**（うち証明書のDNS検証が約2分）／本体スタック **244秒**。

実測：`https://tritome-gennai-sample.com` `https://www.tritome-gennai-sample.com` ともに
**HTTP 200・TLS検証エラーなし・0.04秒**。CloudFrontの既定URLも引き続き有効。

### 本家CDKへの改変（apex対応）

源内のCDKはサブドメイン専用（`${hostName}.${domainName}` 固定）だったため、
ルートドメインで運用するには以下3箇所の改変が必要だった。

| ファイル | 変更 |
|---|---|
| `lib/app-domain-stack.ts` | `hostName` が空ならルートドメインで証明書発行、SANに `www` |
| `lib/construct/web.ts`（代替ドメイン） | apex ＋ `www` を CloudFront に割り当て |
| `lib/construct/web.ts`（Aレコード） | `hostName` 必須を外し、apex は `recordName` 省略。`www` 用も追加 |

**apex に CNAME は張れないが、Route 53 の Alias レコードなら張れる。**

## 残作業

- [ ] Cognito に管理者ユーザーを作成（`UserGroup` + `SystemAdminGroup`）※招待メールが送信される
- [ ] チーム作成 → Ex-App（hoikusho-check）を登録して実機確認
- [ ] Bedrock の Anthropic 利用用途フォーム提出（未提出のためチャット・ExAppともLLM呼び出し不可）
- [ ] Lambdaメモリ512MB上限の緩和申請（現在は CDK Aspect でキャップして回避中）
- [ ] Budgets アラートの設定（新アカウントには未設定）
- [ ] 旧アカウント <OLD_AWS_ACCOUNT_ID> のスタック撤去をどうするか判断
