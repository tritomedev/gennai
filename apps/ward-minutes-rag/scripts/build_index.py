#!/usr/bin/env python3
"""
サンプルデータをチャンク分割し、Bedrock Cohere Embed で埋め込んで
**ファイルのインデックス**を作る（TASK-043）。

Qdrant を使わない理由:
  本POCの規模は 24レコード → 106チャンク程度。ベクトルDBを常時起動するより、
  埋め込み済みベクトルをファイルに固めて Lambda に同梱し、メモリ内で
  コサイン類似度を取るほうが安く・速く・運用が要らない。
  （OpenSearch Serverless 等を使うと月5万円規模の固定費が発生する）

出力:
  data/index/vectors.npy … float32 の正規化済みベクトル（N, 1024）
  data/index/chunks.json … 各ベクトルに対応するメタデータ

使い方:
  .venv/bin/python scripts/build_index.py
"""
import json
from pathlib import Path

import boto3
import numpy as np

APP = Path(__file__).resolve().parent.parent
SAMPLE = APP / "data" / "sample"
OUT_DIR = APP / "data" / "index"

REGION = "ap-northeast-1"
MODEL_ID = "cohere.embed-multilingual-v3"
CHUNK_CHARS = 400        # Cohere embed の512トークン上限に対する安全側の目安
CHUNK_OVERLAP_LINES = 1  # 文脈断絶を緩和する行オーバーラップ
BATCH = 96               # Cohere embed の1リクエスト上限

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def chunk_text(text, title):
    """行境界を尊重して ~CHUNK_CHARS 文字で分割。各チャンク先頭にタイトルを付す。"""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    chunks, cur, cur_len = [], [], 0
    for ln in lines:
        if cur and cur_len + len(ln) > CHUNK_CHARS:
            chunks.append("\n".join(cur))
            cur = cur[-CHUNK_OVERLAP_LINES:] if CHUNK_OVERLAP_LINES else []
            cur_len = sum(len(x) for x in cur)
        cur.append(ln)
        cur_len += len(ln)
    if cur:
        chunks.append("\n".join(cur))
    if not chunks:
        chunks = [text or title]
    return [f"【{title}】\n{c}" if not c.startswith(f"【{title}】") else c
            for c in chunks]


def embed(texts, input_type):
    """Cohere embed をバッチ実行してベクトル配列を返す。"""
    out = []
    for i in range(0, len(texts), BATCH):
        body = json.dumps({"texts": texts[i:i + BATCH],
                           "input_type": input_type, "truncate": "END"})
        resp = bedrock.invoke_model(modelId=MODEL_ID,
                                    contentType="application/json",
                                    accept="application/json", body=body)
        out.extend(json.loads(resp["body"].read())["embeddings"])
    return out


def load_records():
    recs = []
    for name in ("seido.jsonl", "giron.jsonl"):
        p = SAMPLE / name
        if not p.exists():
            print(f"[WARN] {p} が無い。先に fetch_seido.py / build_giron.py を実行して。")
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                recs.append(json.loads(line))
    return recs


def main():
    records = load_records()
    if not records:
        raise SystemExit("サンプルデータが空。")

    chunks = []
    for r in records:
        for idx, ctext in enumerate(chunk_text(r.get("text", ""), r["title"])):
            chunks.append({
                "doc_id": r["id"],
                "chunk_index": idx,
                "text": ctext,
                "source_type": r["source_type"],
                "title": r["title"],
                "url": r["url"],
                "ward": r.get("ward", "港区"),
                "seido_name": r.get("seido_name", ""),
                "updated": r.get("updated", ""),
                "planned_time": r.get("planned_time", ""),
                "session": r.get("session", ""),
                "source": r.get("source", ""),
            })

    n_seido = sum(1 for c in chunks if c["source_type"] == "seido")
    n_giron = sum(1 for c in chunks if c["source_type"] == "giron")
    print(f"レコード {len(records)} 件 → チャンク {len(chunks)} 件 "
          f"(seido={n_seido} / giron={n_giron})")

    print(f"Bedrock {MODEL_ID} で埋め込み中...")
    vectors = np.array(embed([c["text"] for c in chunks], "search_document"),
                       dtype=np.float32)
    # 検索時は内積だけで済むよう、保存時にL2正規化しておく
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / np.maximum(norms, 1e-12)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    np.save(OUT_DIR / "vectors.npy", vectors)
    (OUT_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False), encoding="utf-8")

    v_kb = (OUT_DIR / "vectors.npy").stat().st_size / 1024
    c_kb = (OUT_DIR / "chunks.json").stat().st_size / 1024
    print(f"=> {OUT_DIR} に出力: vectors.npy {v_kb:.0f}KB / chunks.json {c_kb:.0f}KB "
          f"({vectors.shape[0]} x {vectors.shape[1]})")


if __name__ == "__main__":
    main()
