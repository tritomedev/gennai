# echo-observer ローカル単体検証（TASK-002 前半）

> 環境固有の値は `<...>` のプレースホルダにしている。実値は内部管理の `private/environment.md` を参照。


- **検証日:** 2026-07-08
- **ステータス:** ローカル検証完了。**その後 源内Webへの登録・実リクエスト捕捉まで完了**（[exapp-observation-2026-07-08.md](./exapp-observation-2026-07-08.md) 参照）
- **対象:** [apps/echo-observer/](../../apps/echo-observer/) — 源内 観察用リッチエコーアプリ
- **目的:** 源内Webに繋ぐ前に、自作AIアプリ側で源内プロトコルの受け口を作り、想定外リクエストでも壊れず観察できることを確認する

---

## 何を作ったか

源内プロトコル最小要件（`POST /` で `{"inputs": {...}}` を受け `{"outputs": "..."}` を返す）を満たす
**LLM非搭載の観察専用アプリ**。狙いは「源内という器の形を知る」こと。

観察は二段構え：

- **UI向け**: `inputs` を Markdown 整形して `outputs` で返却（画面で即確認）
- **サーバーログ**: 生Body + 全ヘッダーを `requests.log` に記録（未知ヘッダー・想定外キーの捕捉）

file の Base64 本体は返さず先頭48字＋実サイズのみ（UI崩壊・ログ肥大の防止）。

## 環境

| 項目 | 値 |
|---|---|
| Python | 3.9.6 |
| FastAPI / uvicorn | 0.115.6 / 0.34.0（インストール済み） |
| 起動 | `python3 -m uvicorn main:app --host 127.0.0.1 --port 8899` |

---

## 検証結果

### 正常系（源内風サンプル）

`sample-request.json`（question / category=select / agree=checkbox / count=number / file / conversation_history）を POST。

| 観察項目 | 結果 |
|---|---|
| 同期レスポンス `{"outputs": "Markdown"}` | ✅ 画面表示形式を確認 |
| number（`"count": 3`） | ✅ `int` で受信 |
| checkbox複数（`"apple,banana"`） | ✅ カンマ区切り文字列（仕様書通り） |
| file | ✅ Base64デコードで実サイズ算出（51B）、本体は先頭48字のみ |
| conversation_history | ✅ 文字列として受信（疑似チャットの土台OK） |
| ヘッダー二段観察 | ✅ UIは `x-api-key` をマスク／ログは生値記録 |

### 異常系・エッジケース（観察アプリの頑丈さ）

| ケース | HTTP | 挙動 | 学び |
|---|---|---|---|
| A. `{"inputs":{}}`（空） | 200 | 「inputsが空」表示 | — |
| B. `{"foo":"bar"}`（inputs無し） | 200 | UIはA と同一表示だが**ログでは Body を区別** | 二段構えの価値 |
| C. 壊れたJSON | 200 | 落ちずに受理・ログ `body:null` | 本番の異常系でも記録継続 |
| D. 完全に空Body | 200 | 落ちない・`raw_len:0` | 同上 |
| E. `"count":"5"`（数値を文字列で） | 200 | `str` のまま | 型は送信側次第 |
| F. file複数（group跨ぎ） | 200 | 全ファイル列挙・各サイズ算出 | group跨ぎOK |
| G. 深ネスト＋未知ヘッダー | 200 | `dict` も未知ヘッダー（`x-gennai-*`）も捕捉 | **想定外を取りこぼさない** |

**結論:** 全ケースで HTTP 200・クラッシュ無し。源内が仕様書外のヘッダーやキーを送ってきても、
繋いだ瞬間に `requests.log` で全捕捉できる状態になった。

---

## 分かったこと / まだ分からないこと

### 分かったこと
- 自作AIアプリ側の受け口は**FastAPIで数十行**で作れる（仕様書の「ハードルは低い」を実地で確認）。
- `Request` から生Body＋全ヘッダーを取る作りにすれば、型定義に縛られず**想定外も観察できる**。

### まだ分からないこと（源内Web接続後に検証）
> **TODO:** 源内が実際に付けてくるヘッダー（チームID・ユーザー識別子等）の有無と名前
> **TODO:** 源内側が number / checkbox / file をどう型変換して送出するかの実挙動
> **TODO:** `x-api-key` の発行・検証フロー（TASK-005）
> **TODO:** 登録時に指定するエンドポイントパス・タイムアウト・max_size のデフォルト

---

## 次のステップ

✅**完了済み:** 源内Web（AWS。`<OLD_CLOUDFRONT_URL>` で稼働）へ echo-observer を登録し、実リクエストのキャプチャに成功した。仕様書外フィールド（`sessionId`・`x-user-id`）も発見。詳細は [exapp-observation-2026-07-08.md](./exapp-observation-2026-07-08.md)。前提だった TASK-001（genai-web の起動）も AWS デプロイで完了済み（[genai-web-deploy-record.md](./genai-web-deploy-record.md)）。
