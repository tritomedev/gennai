# 源内 AIアプリAPI仕様 調査ログ

- **調査日:** 2026-07-08
- **調査元:** https://github.com/digital-go-jp/genai-web/blob/main/docs/AIアプリAPI仕様.md
- **ステータス:** 完了
- **重要度:** ★★★（自作AIアプリ開発の核心）

> ⚠️ 公式注記: この仕様は2026年3月時点のもので試行錯誤中。今後大きく変わる可能性あり。

---

## 概要

源内WebはREST APIを呼び出す形で外部AIアプリと連携する。
つまり**プロトコルさえ守ればどんな言語・クラウドでも自作AIアプリを源内に追加できる**。

---

## 全体の流れ

```
[ 源内Web UI ]
    ↓ JSON定義（リクエスト形式）を登録
[ チーム管理メニュー ]
    ↓ ユーザーが入力してリクエスト送信
[ 自作AIアプリ（REST API）]
    ↓ outputs を返す
[ 源内Web UI に結果表示 ]
```

---

## 1. リクエスト形式の定義（源内Webへの登録内容）

源内WebのGUIに以下のようなJSONを登録することでUIが自動生成される。

```json
{
  "Request-key1": { <コンポーネント定義> },
  "Request-key2": { <コンポーネント定義> }
}
```

### 使えるUIコンポーネント

| type | 内容 |
|---|---|
| `text` | テキストフィールド（1行） |
| `number` | 数値フィールド |
| `textarea` | テキストエリア（複数行） |
| `file` | ファイルアップロード（Base64送信） |
| `select` | セレクトボックス |
| `checkbox` | チェックボックス |
| `radio` | ラジオボタン |
| `hidden` | 非表示フィールド（内部パラメータ用） |

### 定義例（シンプルなQAアプリ）

```json
{
  "question": {
    "title": "質問",
    "desc": "質問したい内容を入力してください。",
    "type": "text",
    "required": true
  },
  "category": {
    "title": "カテゴリ",
    "type": "select",
    "items": [
      { "title": "法令", "value": "law" },
      { "title": "手続き", "value": "procedure" }
    ]
  }
}
```

---

## 2. 送出されるリクエスト（AIアプリ側が受け取るもの）

源内WebからAIアプリへは `inputs` キーでラップされたJSONが送られる。

```json
{
  "inputs": {
    "question": "ユーザーが入力したテキスト",
    "category": "law",
    "files": [
      {
        "key": "キー名",
        "files": [
          {
            "filename": "ファイル名.pdf",
            "content": "Base64エンコードされたデータ"
          }
        ]
      }
    ]
  }
}
```

### 注意点

- 数値は `""` で囲んでも**数値型**として送られる
- チェックボックス複数選択は `"apple,banana"` のようにカンマ区切り文字列
- ファイルはBase64エンコードで送信される

---

## 3. レスポンス仕様（AIアプリ側が返すもの）

### 同期処理（シンプル）

```json
{
  "outputs": "AIが生成したテキスト（Markdown可）"
}
```

これだけでOK。Markdownも使える。

### 非同期処理（時間がかかる処理向け）

時間のかかる処理（RAG・大量文書処理等）はポーリング方式で対応。

**① 初期リクエスト → 202 Accepted**
```json
{
  "outputs": "リクエストを受け付けました",
  "request_id": "a1b2c3d4-...",
  "status": "PENDING",
  "status_url": "/status/a1b2c3d4-..."
}
```

**② ステータス確認（ポーリング）**
```json
{
  "status": "IN_PROGRESS",
  "progress": "処理中... ステップ 3/5",
  "request_id": "a1b2c3d4-..."
}
```

**③ 完了時**
```json
{
  "status": "COMPLETED",
  "outputs": "処理結果のテキスト（Markdown可）",
  "artifacts": [
    {
      "contents": "Base64エンコードされたPDF等",
      "display_name": "report.pdf"
    }
  ]
}
```

**④ エラー時**
```json
{
  "status": "ERROR",
  "error": {
    "message": "An error occurred during processing.",
    "details": "Required resource not found."
  }
}
```

---

## 4. 会話履歴（疑似チャット）

`conversation_history` キーを追加すると「会話を続ける」ボタンが表示され、チャット形式のやりとりができる。

```json
{
  "question": {
    "type": "text",
    "title": "質問"
  },
  "conversation_history": {
    "title": "会話履歴",
    "type": "textarea"
  }
}
```

---

## 5. 自作AIアプリを作るための最小実装

Python（FastAPI）の場合の最小構成：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Inputs(BaseModel):
    question: str

class Request(BaseModel):
    inputs: Inputs

@app.post("/ask")
def ask(req: Request):
    # ここでLLMを呼び出す
    answer = call_llm(req.inputs.question)
    return {"outputs": answer}
```

これだけで源内Webに登録できる最小のAIアプリが完成する。

---

## 重要な気づき・まとめ

| 項目 | 内容 |
|---|---|
| **認証** | `x-api-key` ヘッダーで認証 |
| **プロトコル** | REST API（JSON） |
| **レスポンス形式** | `outputs` キーにテキスト（Markdown可） |
| **ファイル** | Base64エンコードで双方向やりとり |
| **非同期対応** | ポーリング方式（request_id + status_url）|
| **チャット対応** | `conversation_history` キーで実現 |
| **自由度** | 言語・クラウド・LLMは完全に自由 |

**結論: 自作AIアプリのハードルはかなり低い！**
`POST /endpoint` で `{"outputs": "テキスト"}` を返すだけで動く。

---

## TODO

> **TODO:** 認証（x-api-key）の発行・管理方法を確認する
> **TODO:** 非同期処理のタイムアウト設定を確認する
> **TODO:** ファイルのmax_sizeのデフォルト値を確認する
> **TODO:** Lawsyの実装がこのプロトコルにどう準拠しているか確認する（次の調査へ）
