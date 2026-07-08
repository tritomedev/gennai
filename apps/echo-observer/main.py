"""
源内（GenAI） 観察用リッチエコーアプリ (TASK-002)

目的:
  源内Webが自作AIアプリへ「実際に」何を送ってくるかを丸裸にする。
  - UI向け : 受け取った inputs を Markdown 整形して {"outputs": ...} で返す（画面で即確認）
  - ログ   : 生Body + 全ヘッダーを標準出力 & requests.log に記録（仕様書に無い情報を捕まえる）

源内プロトコル最小要件:
  POST /  で {"inputs": {...}} を受け、{"outputs": "テキスト(Markdown可)"} を返すだけ。

注意:
  file コンポーネントの Base64 本体は返さない/ログにも先頭のみ（UI崩壊・ログ肥大の防止）。
"""

import base64
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request

app = FastAPI(title="源内 観察用リッチエコー (echo-observer)")

LOG_FILE = Path(__file__).parent / "requests.log"
B64_PREVIEW = 48  # Base64 本体はこの文字数だけ記録/表示する


def _decoded_size(b64: str) -> int:
    """Base64 文字列をデコードした実バイト数を返す（壊れていても概算で耐える）。"""
    try:
        return len(base64.b64decode(b64, validate=False))
    except Exception:
        return -1


def _human_size(n: int) -> str:
    if n < 0:
        return "デコード不可"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n/1:.0f}{unit}"
        n /= 1024
    return f"{n}B"


def _summarize_files(files_field) -> str:
    """inputs['files'] を人間が読める要約に。Base64本体は出さない。"""
    lines = []
    for group in files_field or []:
        key = group.get("key", "(no key)")
        for f in group.get("files", []):
            b64 = f.get("content", "") or ""
            size = _decoded_size(b64)
            lines.append(
                f"- key=`{key}` / **{f.get('filename', '(no name)')}** "
                f"/ 実サイズ≈{_human_size(size)} "
                f"/ base64先頭: `{b64[:B64_PREVIEW]}…`"
            )
    return "\n".join(lines) if lines else "_(ファイルなし)_"


def build_markdown(headers: dict, inputs: dict) -> str:
    """観察結果を UI 表示用 Markdown に整形する。"""
    md = ["# 🔍 源内からのリクエスト観察結果", ""]

    # --- inputs 本体 ---
    md.append("## inputs（ユーザー入力）")
    if not inputs:
        md.append("_inputs が空、または JSON パース失敗_")
    else:
        md.append("| キー | 型 | 値 |")
        md.append("|---|---|---|")
        for k, v in inputs.items():
            if k == "files":
                md.append(f"| `files` | {type(v).__name__} | ↓ 別掲 |")
                continue
            shown = str(v)
            if len(shown) > 120:
                shown = shown[:120] + "…"
            md.append(f"| `{k}` | `{type(v).__name__}` | {shown} |")

    # --- files ---
    if "files" in inputs:
        md += ["", "## files（アップロードファイル）", _summarize_files(inputs.get("files"))]

    # --- headers（源内が付けてくるヘッダーの観察）---
    md += ["", "## 受信ヘッダー"]
    for k, v in headers.items():
        # x-api-key など秘匿値はマスク
        shown = v if k.lower() not in ("x-api-key", "authorization") else v[:4] + "***"
        md.append(f"- `{k}`: {shown}")

    return "\n".join(md)


def log_observation(headers: dict, raw: bytes, payload):
    """生リクエストを標準出力 & ファイルへ。files の Base64 本体は切り詰める。"""
    safe_payload = payload
    try:
        if isinstance(payload, dict) and "inputs" in payload:
            safe_payload = json.loads(json.dumps(payload))  # deep copy
            for group in safe_payload["inputs"].get("files", []) or []:
                for f in group.get("files", []):
                    if "content" in f:
                        f["content"] = f["content"][:B64_PREVIEW] + f"…(len={len(f['content'])})"
    except Exception:
        pass

    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "headers": headers,
        "raw_len": len(raw),
        "body": safe_payload,
    }
    line = json.dumps(record, ensure_ascii=False, indent=2)
    print("\n===== 📥 REQUEST OBSERVED =====\n" + line + "\n==============================\n", flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as fp:
        fp.write(line + "\n")


@app.post("/")
async def echo(request: Request):
    raw = await request.body()
    headers = dict(request.headers)
    try:
        payload = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        payload = None

    inputs = (payload or {}).get("inputs", {}) if isinstance(payload, dict) else {}
    log_observation(headers, raw, payload)

    return {"outputs": build_markdown(headers, inputs)}


@app.get("/")
def health():
    """疎通確認用。ブラウザ/GETでも生きてるか分かるように。"""
    return {"status": "ok", "app": "echo-observer", "hint": "POST / に {\"inputs\": {...}} を投げてね"}
