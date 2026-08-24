#!/usr/bin/env python3
"""
サンプルデータ（現行制度 / 議論中）をチャンク分割し、
Bedrock Cohere Embed Multilingual v3 で埋め込んで Qdrant に投入する。（TASK-007）

設計上の要点:
  - Cohere embed-multilingual-v3 の入力上限は 512 トークン。
    制度ページ本文は最大約8,000文字あるため、分割せずに投げると大半が
    切り捨てられて検索に載らない。→ 行境界を尊重した ~400文字チャンクに分割する。
  - Cohere は search_document / search_query を撃ち分けられる（非対称検索）。
    投入側は search_document、検索側は search_query を使う。
  - source_type（seido / giron）を payload に持たせ、Ex-App の2段出力
    （現行制度 / 議論中の動向）で出し分ける。

使い方:
  .venv/bin/python scripts/ingest_qdrant.py
"""
import json
import uuid
from pathlib import Path

import boto3
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

APP = Path(__file__).resolve().parent.parent
SAMPLE = APP / "data" / "sample"

REGION = "ap-northeast-1"
MODEL_ID = "cohere.embed-multilingual-v3"
DIM = 1024
COLLECTION = "minato_kosodate"

QDRANT_URL = "http://localhost:6333"
CHUNK_CHARS = 400        # 512トークン上限に対する安全側の目安
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
    # 各チャンクにタイトルを付けて単体でも文脈が立つようにする
    return [f"【{title}】\n{c}" if not c.startswith(f"【{title}】") else c
            for c in chunks]


def embed(texts, input_type):
    """Cohere embed をバッチ実行してベクトル配列を返す。"""
    out = []
    for i in range(0, len(texts), BATCH):
        batch = texts[i:i + BATCH]
        body = json.dumps({
            "texts": batch,
            "input_type": input_type,
            "truncate": "END",
        })
        resp = bedrock.invoke_model(
            modelId=MODEL_ID, contentType="application/json",
            accept="application/json", body=body,
        )
        payload = json.loads(resp["body"].read())
        out.extend(payload["embeddings"])
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

    # --- チャンク化 ---
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
                # 制度側 / 議論中側それぞれのメタ
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

    # --- 埋め込み ---
    print(f"Bedrock {MODEL_ID} で埋め込み中...")
    vectors = embed([c["text"] for c in chunks], "search_document")
    print(f"埋め込み完了: {len(vectors)} 本 / {len(vectors[0])} 次元")

    # --- Qdrant 投入 ---
    client = QdrantClient(url=QDRANT_URL)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )
    points = [
        PointStruct(id=str(uuid.uuid4()), vector=v, payload=c)
        for c, v in zip(chunks, vectors)
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    info = client.get_collection(COLLECTION)
    print(f"=> Qdrant '{COLLECTION}' に投入完了: {info.points_count} points")


if __name__ == "__main__":
    main()
