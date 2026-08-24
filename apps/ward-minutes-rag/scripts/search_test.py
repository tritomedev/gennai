#!/usr/bin/env python3
"""
Qdrant の検索動作を確認する（TASK-007 の検証）。

ユースケースの2段構え（現行制度 / 議論中の動向）が実際に引けるかを、
source_type ごとに検索して確認する。ここで作った retrieve() は
そのまま Ex-App（TASK-034）の検索コアに流用する想定。

使い方:
  .venv/bin/python scripts/search_test.py "子どもの補助金についてなにか無いかな？"
"""
import json
import sys

import boto3
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

REGION = "ap-northeast-1"
MODEL_ID = "cohere.embed-multilingual-v3"
COLLECTION = "minato_kosodate"
QDRANT_URL = "http://localhost:6333"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)
client = QdrantClient(url=QDRANT_URL)


def embed_query(text):
    body = json.dumps({
        "texts": [text], "input_type": "search_query", "truncate": "END",
    })
    resp = bedrock.invoke_model(
        modelId=MODEL_ID, contentType="application/json",
        accept="application/json", body=body,
    )
    return json.loads(resp["body"].read())["embeddings"][0]


def retrieve(query, source_type=None, limit=5, group_size=2):
    """source_type で絞り、doc_id ごとにグループ化して検索する。

    グループ化しないと、チャンク数の多い長い制度ページが上位を独占し、
    「補助金は何がある？」に対して1制度の断片だけが並ぶ事故が起きる。
    doc_id 単位で束ねることで制度の多様性を確保する。
    """
    flt = None
    if source_type:
        flt = Filter(must=[FieldCondition(
            key="source_type", match=MatchValue(value=source_type))])
    return client.query_points_groups(
        collection_name=COLLECTION,
        query=embed_query(query),
        group_by="doc_id",
        limit=limit,           # 何件の「制度/話題」を返すか
        group_size=group_size,  # 1制度あたり何チャンク添えるか
        query_filter=flt,
        with_payload=True,
    ).groups


def show(title, groups):
    print(f"\n===== {title} =====")
    for i, g in enumerate(groups, 1):
        top = g.hits[0]
        p = top.payload
        meta = p.get("updated") or p.get("planned_time") or p.get("session") or "-"
        body = p["text"].replace("\n", " ")
        print(f"[{i}] score={top.score:.4f} | {p['title']} | {meta} "
              f"| chunks={len(g.hits)}")
        print(f"    {body[:110]}...")


def main():
    q = sys.argv[1] if len(sys.argv) > 1 else "子どもの補助金についてなにか無いかな？"
    print(f"質問: {q}")
    show("① 現行制度（AsIs / source_type=seido）", retrieve(q, "seido", 5))
    show("② 議論中・今後の方針（source_type=giron）", retrieve(q, "giron", 5))


if __name__ == "__main__":
    main()
