# ExApp実機観察：源内が送る実リクエスト捕捉（TASK-002 完了）

- **観察日:** 2026-07-08
- **ステータス:** 完了（源内Webに自作ExApp登録 → 実リクエスト捕捉に成功）
- **観察対象:** echo-observer（[apps/echo-observer/](../../apps/echo-observer/)）
- **接続構成:** 源内Web(AWS Lambda) → cloudflaredクイックトンネル → ローカルのecho-observer

---

## 何をしたか

1. 源内Web（デプロイ済み）にログインし、チームを作成
2. echo-observer を cloudflared 一時トンネルで公開（`https://xxxx.trycloudflare.com`）
3. 源内Webの[アプリの作成]でExApp登録
   - エンドポイントURL: トンネルの公開URL
   - APIキー: ダミー（echo-observerは検証せず、観察対象として記録）
   - リクエスト定義: `question` テキストフィールド1つ
4. 登録アプリから質問を送信 → 源内のLambdaがecho-observerを実際に呼び出し
5. echo-observer の `requests.log`（生Body＋全ヘッダー）で捕捉

---

## 捕捉した実リクエスト（生データ）

```json
{
  "headers": {
    "user-agent": "node",
    "x-api-key": "dummy-key-123",
    "x-user-id": "ZVKR-SY7prVL5b4l8WFb-Vcafge0uhQIvOJ4e-3CVeo",
    "cf-connecting-ip": "13.158.55.104",
    "content-type": "application/json",
    "...": "（cf-* はCloudflare中継由来）"
  },
  "body": {
    "inputs": { "question": "源内AIってなにができるの？" },
    "sessionId": "a92b585e-cfab-4447-96d1-7bb024efdefc"
  }
}
```

---

## 判明した「公式仕様書に無い」フィールド（本観察の最大の収穫）

| 発見 | 値の例 | 意味・活用 |
|---|---|---|
| **`sessionId`（body直下）** | `a92b585e-...`（UUID） | `inputs`と並んでbody直下。会話セッション追跡用と推測。疑似チャット実装のヒント |
| **`x-user-id`（ヘッダー）** | `ZVKR-SY7prVL5b4l8...` | ユーザーのHMAC識別子（源内の`UserIdentifierHmacKey`＝セッションハイジャック対策由来）。**PIIを晒さずExApp側でユーザー識別可能** → RAGのユーザー別分離・利用制限に活用可 |

→ 仕様書（[ai-app-api-spec.md](../02_research/ai-app-api-spec.md)）に反映済み。

## 仕様通り／構成通りを実機確認できたこと

- `inputs` ラッパー＋定義したフィールド（`question`）で届く ← プロトコル仕様通り
- `x-api-key` に登録時のキーがそのまま入る ← ExApp認証の仕組み（TASK-005の実機確認）
- `user-agent: node` ← 源内の呼び出しLambdaはNode.jsランタイム
- 送信元IPはAWS帯（`13.158.55.104`）で毎回変動 ← **VPC撤廃構成のため固定EIPなし**（設計通りの挙動を実証）
- 同期レスポンス `{"outputs": "Markdown"}` を源内が受理し画面表示

---

## 設計判断が報われた点：二段構え観察の有効性

- **UI向けMarkdown**（`outputs`）には `sessionId` が出なかった（inputs以外のbody直下キーを描画していなかったため）
- **サーバーログ**（`requests.log`）が `sessionId` を捕捉
- → 「UI向け＋サーバーログの二段構え」設計により、**UIでは見えない仕様外フィールドを取りこぼさなかった**。観察アプリ設計時の狙い通り。

> **改善余地（任意）:** echo-observer の `build_markdown` を、inputs以外のbody直下キーも表示するよう拡張するとUIだけでも気づけるようになる。

---

## 次のステップ

- [ ] `x-user-id` / `sessionId` を活用したExApp設計（ユーザー別RAG等）
- [ ] エコー返しを実LLM（Ollama/Claude）に差し替え
- [ ] 会話履歴（conversation_history）フィールドの実挙動確認（複数ターン送信）
- [ ] 継続運用するなら echo-observer を公開サーバー（VPS等）へ（cloudflaredトンネルは一時的）
