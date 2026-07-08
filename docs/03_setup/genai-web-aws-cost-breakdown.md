# genai-web AWSコスト内訳（synth実データ）

- **作成日:** 2026-07-08
- **ステータス:** 確定（`cdk synth` で生成した実テンプレートから集計）
- **前提構成:** 最小コスト構成パラメータ（[genai-web-minimal-param-design.md](./genai-web-minimal-param-design.md)）でsynthした結果
- **関連:** [genai-web-aws-requirements.md](./genai-web-aws-requirements.md) / [aws-cost-guardrails.md](./aws-cost-guardrails.md)
- **通貨換算:** 1USD = ¥150 で概算（`cdk.json` の costConversion と同じレート）

> ⚠️ 金額はap-northeast-1（東京）の料金からの概算。正確な単価はAWS料金ページで確認すること。

---

## NAT Gateway とは何か（用語解説）

固定費の主因なので先に説明する。

1. **VPC** = AWS内に作る「隔離されたプライベートネットワーク」。外から勝手に入れない安全な区画。
2. 源内は **ExApp（自作AIアプリ）を叩くLambdaを、あえてVPCの中に閉じ込める**設計。
3. 理由 = **送信元IPを固定するため**。ExApp側で「この固定IP（源内）からのアクセスだけ許可」というセキュリティ制御を可能にする（行政システムらしい堅牢設計）。
4. VPCの中は既定でインターネットに出られない。外にあるExAppを叩くには有料の出口 = **NAT Gateway** が必要。
5. NAT Gatewayは**設置するだけで時間課金**（約¥6,800/月/個）。源内は高可用性のためAZ（データセンター）2箇所に1個ずつ = **2個** → 約¥13,500/月。

→ この「ExAppを安全に叩くための専用ネットワーク設備」が固定費の正体。

---

## 全リソース一覧（synth実データ）

`cdk synth`（env=-selfHostingDev）が生成した3スタックのテンプレートから、全リソースタイプを集計した結果。

### 🔴 固定費グループ（デプロイして放置してもかかる）

| サービス | 数 | 月額目安 | 用途 |
|---|---|---|---|
| **NAT Gateway** | 2 | **~¥13,500** | ExApp呼び出しLambdaのネット出口 |
| **VPCインターフェースエンドポイント** | 1 | ~¥3,000 | VPC内からSecrets Managerへ接続 |
| KMS暗号鍵 | 2 | ~¥300 | データ暗号化 |
| CloudWatchアラーム / ログ / VPC FlowLog | 数個 | ~¥300 | 監視・ログ |
| VPC / サブネット×4 / IGW / ルートテーブル | 一式 | ¥0 | ネットワーク土台（箱自体は無料） |
| **固定費 合計** | | **~¥17,000/月** | **うち約¥16,500がExApp用VPC由来** |

### 🟢 従量課金グループ（テスト利用想定の金額）

**テスト利用の想定シナリオ:** 数日〜1ヶ月、チャット約200〜500回（haiku/nova中心）、小さいファイル数個、UIアクセス数百回、デプロイ数回。

| サービス | 数 | アイドル | テスト利用時の目安 |
|---|---|---|---|
| Lambda関数 | 53 | ¥0 | **¥0**（無料枠100万回/月に対し数千回） |
| API Gateway (REST) | 2 | ¥0 | **¥0**（無料枠内） |
| DynamoDB | 4 | ~¥0 | **¥0〜¥10**（オンデマンド・少量） |
| S3バケット | 9 | 数円 | **¥0〜¥10**（数MB保存） |
| CloudFront | 1 | ¥0 | **¥0**（無料枠1TB/月） |
| Cognito | 1 | ¥0 | **¥0**（5万MAUまで無料） |
| SQS / SNS | 3 | ¥0 | **¥0**（無料枠内） |
| **Bedrock（推論プロファイル×3）** | 3 | ¥0 | **¥100〜¥500**（チャット200〜500回、haiku/nova） |
| Bedrock画像生成（Nova Canvas） | – | ¥0 | 使えば **¥120〜240**（20枚程度）／使わなければ¥0 |
| CodeBuild | 1 | ¥0 | **¥0**（デプロイ時のビルド・無料枠内） |
| **従量 合計（テスト利用）** | | | **~¥100〜¥700/月**（ほぼBedrock） |

#### Bedrockトークン代の内訳（テスト想定の計算根拠）

- 1チャット ≈ 入力500 + 出力500トークンと仮定
- Claude Haiku で200回 ≈ 入力0.1M + 出力0.1M ≈ $0.60 ≈ **¥90**
- Nova Lite なら同条件で ≈ **¥10** 程度（さらに安い）
- 1000回まで叩いても Haiku で ≈ ¥450 程度
- opus-4-8 は単価が十数倍なので今回のmodelIdsからは除外済み

---

## 結論：固定費はほぼ「ExApp用VPC」一点

> 固定費 ¥17,000/月 のうち **約¥16,500（97%）が ExApp用VPC（NAT×2 + エンドポイント）** に集中。
> それを除けば源内Web全体の固定費は **実質¥数百/月**。変動はBedrock（テスト利用で¥数百）のみ。

**コスト最適化 = このVPC/NATをどうするかの一点に尽きる。** 他リソースは気にしなくてよい。

---

## VPC/NAT 対策オプションと月額シナリオ

| 案 | 内容 | NAT | 月額（固定＋テスト利用） | 手間 |
|---|---|---|---|---|
| **A. そのまま→検証後destroy** | NAT2個のままデプロイ、数日検証後 `cdk destroy` | 2 | 1週間なら実費 **~¥4,000** | 改変ゼロ |
| **B. `maxAzs:1` に改変** | NAT1個に半減（フォークで1行変更） | 1 | **~¥9,000/月** | 1行変更 |
| **C. 会社の既存VPCを指定** | `vpcIdForInvokeExApp` に既存VPC ID | 新規0 | **~¥600/月＋Bedrock** | VPC ID確認 |
| （参考）放置1ヶ月・NAT2個 | 撤去せず1ヶ月起動 | 2 | **~¥17,500/月** | – |

- **A案**の実費内訳（1週間）: NAT ¥3,000 + エンドポイント ¥700 + Bedrock ¥300 ≈ ¥4,000
- **B案**: NAT ¥6,800 + エンドポイント ¥1,500 + その他 ¥600 + Bedrock ¥500 ≈ ¥9,400/月
- **C案**: 既存VPCを使うとInvokeExAppLambdaVpc構文自体が作られない（NAT・エンドポイントとも新規ゼロ）。KMS/ログ ¥600 + Bedrock のみ

### 改変ポイント（B案の場合）

`packages/cdk/lib/construct/team-access-control.ts` の以下を `2` → `1`：

```typescript
const invokeExAppVpc = new InvokeExAppLambdaVpc(this, 'InvokeExAppVpc', {
  encryptionKey: props.encryptionKey,
  maxAzs: 1,        // ← 2 から 1 に（NATを1個に）
  cidr: '10.0.0.0/16',
  cidrMask: 24,
});
```

---

## ✅ 採用結果：①案（VPC撤廃）を実装・synth実証済み（2026-07-08）

POC用途のため **①案（ExApp呼び出しLambdaをVPCから外す）を実装**。`cdk synth` で固定費リソースの消滅を確認した。

### 実装内容（フォーク改変）

| ファイル | 変更 |
|---|---|
| `packages/cdk/lib/construct/team-access-control.ts` | `vpcId === 'DISABLED'` 分岐を追加。VPC生成をスキップし、2つのExApp Lambda（InvokeExApp / PollExAppStatus）から `vpc`/`vpcSubnets` を外す（`vpcLambdaProps` スプレッド） |
| `packages/cdk/env-parameters/self-hosting-dev.ts` | `vpcIdForInvokeExApp: 'DISABLED'` |

### synth実証結果（before → after）

| リソース | before（VPCあり） | after（①実装後） |
|---|---|---|
| NAT Gateway | 2 | **0** ✅ |
| VPC / サブネット / IGW / ルート | 一式 | **0** ✅ |
| EIP | 2 | **0** ✅ |
| VPCエンドポイント | 1 | **0** ✅ |
| EC2系リソース 全体 | 多数 | **0** ✅ |
| KMS鍵（残る固定費） | 2 | 2（約¥300/月） |
| ExApp呼び出しLambda | あり（VPC内） | **あり（VPC外で稼働）** ✅ |

→ **固定費 ¥17,000/月 → 実質¥600/月**（KMS＋ログのみ）。変動はBedrock（テスト利用¥数百）のみ。

---

## ⚠️ POC限定の割り切り（本番では必ず戻すこと）

**①案はPOC（技術検証）専用の割り切り**。本番運用に移す際は VPC/NAT を戻すこと。理由：

| 観点 | POC（①案・VPCなし） | 本番で戻すべき理由 |
|---|---|---|
| 送信元IP固定 | なし | ExApp側でIP許可リスト運用をするなら固定IP（NAT/NATインスタンス）が要る |
| VPC隔離 | なし | 本番のセキュリティ標準としてLambdaのネットワーク隔離が望ましい |
| データ経路 | AWS管理NW直 | 監査・コンプライアンス要件次第でVPC内経路が求められる場合あり |

### 本番へ戻す手順

- `self-hosting-dev.ts` の `vpcIdForInvokeExApp` を `''`（新規VPC生成）または既存VPC IDに変更するだけ
- コード側の `'DISABLED'` 分岐はそのまま残しても無害（発火しなくなる）

### なぜPOCでは外して安全か（セキュリティ確認済み）

- VPC撤去は**Lambdaの「出口（アウトバウンド）」経路のみ変更**。「入口（インバウンド）」は不変（Lambdaは元々直接到達不可・API Gateway＋Cognitoの裏）
- 乗っ取り対象の常時起動サーバーが存在しない（フルサーバーレス）。VPCを外すことで**新たな侵入口は増えない**
- SSRF被害範囲はむしろ縮小（横移動する内部NWが無い）。加えて源内は**アプリ層でSSRF対策**あり（`lambda/utils/exAppUrlSecurity.ts`：localhost拒否・プライベートIP帯ブロック・制御文字/URL長制限）

---

## 検証方法（この数字の出し方）

デプロイ前に固定費リソースを無料で洗い出す手順（認証情報不要）：

```bash
cd genai-web
export CDK_DEFAULT_ACCOUNT=123456789012   # ダミーでOK（synthは認証不要）
export CDK_DEFAULT_REGION=ap-northeast-1
npm -w packages/cdk run cdk -- synth --all -c env=-selfHostingDev

# 生成テンプレートから固定費リソースを確認
cd packages/cdk/cdk.out
grep -h '"Type": "AWS::' *.template.json | sed -E 's/.*"Type": "([^"]+)".*/\1/' | sort | uniq -c | sort -rn
grep -l "AWS::EC2::NatGateway" *.template.json   # NATの有無
```
