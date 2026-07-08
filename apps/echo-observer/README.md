# echo-observer — 源内 観察用リッチエコーアプリ

源内（GenAI）Web が自作AIアプリ（ExApp）へ**実際に何を送ってくるか**を丸裸にするための最小アプリ。
LLM は繋がない（源内プロトコルの挙動観察に集中するため）。TASK-002 のローカル検証用。

## これは何をする？

源内プロトコル最小要件（`POST /` で `{"inputs": {...}}` を受け `{"outputs": "..."}` を返す）を満たしつつ、
受け取ったリクエストを **二段構え** で観察する：

- **UI向け**: `inputs` を Markdown 整形して `outputs` で返す（源内Web画面で即確認）
- **サーバーログ**: 生Body + **全ヘッダー** を標準出力 & `requests.log` に記録
  （仕様書に載っていない未知ヘッダー・想定外キーを取りこぼさない）

file の Base64 本体は返さず先頭のみ＋実サイズだけ表示（UI崩壊・ログ肥大の防止）。

## 起動

```bash
cd apps/echo-observer
python3 -m uvicorn main:app --host 127.0.0.1 --port 8899
```

## 叩く

```bash
U="http://127.0.0.1:8899/"

# ヘルスチェック
curl -s $U | python3 -m json.tool

# 基本形
curl -s -X POST $U -H "Content-Type: application/json" \
  -d '{"inputs":{"question":"好きな質問"}}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['outputs'])"

# サンプルJSONを丸ごと
curl -s -X POST $U -H "Content-Type: application/json" \
  -d @sample-request.json \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['outputs'])"

# サーバーが記録した生ログ（マスク前ヘッダー・全Body）
cat requests.log
```

## ファイル

| ファイル | 役割 |
|---|---|
| `main.py` | 本体（FastAPI） |
| `sample-request.json` | 源内風のサンプルリクエスト（number/checkbox/file/会話履歴入り） |
| `requests.log` | 観察ログ（自動生成、gitignore対象想定） |

## 検証結果

ローカル単体テストの詳細は [docs/04_build/echo-observer-local-verification.md](../../docs/04_build/echo-observer-local-verification.md) 参照。

## TODO（源内Web接続後にやること）

- [ ] 源内Web（AWS）に登録し、**実際の**リクエスト形式・ヘッダーを `requests.log` でキャプチャする（TASK-002 の残り）
- [ ] `x-api-key` の実際の発行・検証フローを確認する（TASK-005）
- [ ] 源内側が number/checkbox をどう型変換して送ってくるか実挙動を確認する
