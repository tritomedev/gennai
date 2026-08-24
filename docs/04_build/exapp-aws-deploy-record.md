# Ex-App AWSデプロイ記録（hoikusho-check / ward-minutes-rag）

> 環境固有の値は `<...>` のプレースホルダにしている。実値は内部管理の `private/environment.md` を参照。


- **デプロイ日:** 2026-08-22
- **ステータス:** 2アプリともデプロイ成功・稼働中（Bedrockは2026-08-24に全モデル開通）
- **アカウント:** <AWS_ACCOUNT_ID> / リージョン ap-northeast-1（東京）※源内Web本体の <OLD_AWS_ACCOUNT_ID> とは別アカウント
- **IAM:** user/noda（CLIプロファイル `gennai-prod`）

---

## アクセス情報

| 項目 | 値 |
|---|---|
| **Function URL** | <HOIKUSHO_CHECK_URL> |
| APIキー | Secrets Manager `gennai/exapp/hoikusho-check/api-key`（40文字・CDKが自動生成） |
| CloudFormationスタック | `GennaiExApps` |
| モデル | `jp.anthropic.claude-haiku-4-5-20251001-v1:0` |

APIキーの取得：

```bash
aws secretsmanager get-secret-value --secret-id gennai/exapp/hoikusho-check/api-key \
  --query SecretString --output text --profile gennai-prod
```

---

## 構成

```
源内Web ──POST(x-api-key)──> Lambda Function URL ──> Bedrock
                                  ↑ コンテナイメージ（ECR）
                                  実行ロールでBedrockを呼ぶ（アクセスキー不要）
```

- **Lambda（コンテナイメージ / arm64 / 512MB / タイムアウト30秒）**。ローカルの `uvicorn main:app` と
  同じ FastAPI アプリを Mangum 経由で動かすため、コードはローカルと共通。
- **Function URL は `authType=NONE`**。源内Webは `x-api-key` ヘッダーしか送らないため、
  認証はアプリ側（`main.py` の `_authorized`）で行う。キーの実体は Secrets Manager にあり、
  Lambda起動時に1回だけ取得する（環境変数には ARN のみ）。
- **タイムアウト30秒**は源内Web側の ExApp 呼び出しタイムアウト（29秒）より少し長く、源内側が先に切れる。
- **メモリ512MB**は新規AWSアカウントのLambdaメモリ上限に合わせた値。上限緩和後は引き上げ可能。
- IaC は `apps/infra/`（CDK TypeScript）。源内Web本体のスタックとはライフサイクルを分離している。

## デプロイ手順（実施済み）

```bash
aws configure --profile gennai-prod          # アクセスキー登録
cd apps/infra
npm install
npx cdk bootstrap --profile gennai-prod      # アカウント初回のみ
npx cdk deploy --profile gennai-prod
```

デプロイ時間：bootstrap 約1分／deploy 約90秒（うちDockerイメージのビルドとECRプッシュ）。

---

## 動作確認の結果（2026-08-22）

| 確認項目 | 結果 |
|---|---|
| `GET /`（health、コールドスタート込み） | **200 / 2.57秒** |
| `POST /` 認証なし | **401**（想定どおり拒否） |
| `POST /` 認証あり・相談モード | **200 / 1.44秒**。Claude Haiku 4.5 が就労証明書の発行期限を回答、免責付き |
| `POST /` 認証あり・画像OCRチェック | Bedrock 側のエラーで失敗（下記） |

ローカルでは事前に Lambda Runtime Emulator（`docker run` + RIE）で
`GET /` `GET /schema` `POST /` の全てが 200 になることを確認してからデプロイした。

---

## 詰まったこと

### 1. Bedrock「Anthropic の利用用途フォーム」が新アカウントで未提出

```
ResourceNotFoundException: Model use case details have not been submitted for this account.
Fill out the Anthropic use case details form before using the model.
If you have already filled out the form, try again in 15 minutes.
```

- **アカウント単位の手続き**。Lambda からもローカルからも同じエラーになるため、実行環境の問題ではない。
- 時系列：デプロイ直前の疎通確認では `jp.anthropic.claude-haiku-4-5` の呼び出しが成功し、
  本番 Lambda でも相談モードが1回正常に応答した。**その直後から上記エラーに変わった**。
  新規アカウントの検証（verification）が進み、フォーム提出が必須の状態になったと考えられる。
- 対処：Bedrock コンソール → モデルアクセス → Anthropic モデルの利用用途フォームを提出する。

### 2. 新規アカウントでは Bedrock の他モデルも順次開放される

デプロイ前の実測では、同じアカウント・同じリージョンで結果が分かれた：

| モデル | 結果 |
|---|---|
| `jp.anthropic.claude-haiku-4-5` | 呼び出し成功（その後フォーム未提出エラーに変化） |
| `amazon.nova-lite-v1:0` | `AccessDeniedException: Your account is currently being verified` |
| `cohere.embed-multilingual-v3` | 同上 |

`cohere.embed-multilingual-v3` は ward-minutes-rag の埋め込みに必須のため、
**同アプリのAWS移設は cohere が開通してから**着手する。

---

## 撤去方法

```bash
cd apps/infra
npx cdk destroy --profile gennai-prod
```

---

---

# 2本目: ward-minutes-rag（2026-08-24 / TASK-043）

| 項目 | 値 |
|---|---|
| **Function URL** | <WARD_RAG_URL> |
| APIキー | Secrets Manager `gennai/exapp/ward-minutes-rag/api-key` |
| モデル | LLM: `jp.anthropic.claude-haiku-4-5` / 埋め込み: `cohere.embed-multilingual-v3` |

同じ `ExApp` construct を再利用しているため、CDKへの追加は10行程度で済んだ。

## ベクトルDBを使わない構成

Qdrant（Docker）依存を外し、**埋め込み済みベクトルをイメージに同梱**してメモリ内検索する。

```
scripts/build_index.py  … チャンク化＋Cohere埋め込み → data/index/
  ├ vectors.npy   424KB（106 x 1024、L2正規化済みfloat32）
  └ chunks.json   136KB（メタデータ）
        ↓ Dockerfile で COPY
rag.retrieve()          … numpy で内積（＝コサイン類似度）→ doc_idでグループ化
```

- **保存時にL2正規化**しておくことで、検索時は `vectors @ q` の内積だけで済む。
- Qdrant の `query_points_groups(group_by="doc_id", limit, group_size)` と**同じ挙動**を再現したため、
  下流（`_group_to_source` 以降）は一切変更していない。
- この規模（106チャンク）でOpenSearch Serverless等を使うと月5万円規模の固定費になる。**割に合わない**。

## 実測（2026-08-24）

| 確認項目 | 結果 |
|---|---|
| `GET /`（コールドスタート込み） | **200 / 4.3秒**（chunks=106 を読み込み） |
| `POST /` 認証なし | **401** |
| `POST /` RAG実行 | **200 / 6.9秒**、2,339文字の2段構え回答 |

## 詰まったこと：2本目で認証の実装を移植し忘れた

初回デプロイ時、**認証なしのPOSTが200を返した**（1本目は401）。

- 原因: `main.py` の `EXAPP_API_KEY = os.environ.get("EXAPP_API_KEY", "")` のままで、
  CDKが渡している `EXAPP_API_KEY_SECRET_ARN` を読んでいなかった。
  `_authorized()` は**キーが空なら常にTrueを返す**（ローカル開発用の分岐）ため、認証が素通りする。
- 影響: 修正デプロイまでの数分間、Function URL が無認証で公開された状態だった。
- 対処: 1本目と同じ `_load_api_key()`（Secrets Managerから起動時に1回取得）を移植。

**教訓: Ex-Appを追加したら、必ず「認証なしPOSTで401」を確認してからURLを配ること。**
`EXAPP_API_KEY` が空のときに素通りする設計は、ローカル開発には便利だが公開時は危険側に倒れる。

## 次のステップ

- [ ] Bedrock の Anthropic 利用用途フォームを提出し、LLM呼び出しを復旧する
- [ ] 源内Web本体を新アカウント（<AWS_ACCOUNT_ID>）にデプロイする（現在は旧アカウントのみ）
- [ ] 源内Webに Function URL と APIキーを登録して実機確認
- [ ] ward-minutes-rag の Qdrant 依存を外して同じ構成に載せる（cohere 開通後）
