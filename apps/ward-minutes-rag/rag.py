"""
議事録RAGのコア（検索＋回答生成）。main.py と scripts/search_test.py で共用する。

設計上の要点（TASK-007の実測知見に基づく）:
  - doc_id でグループ化して検索する。しないと長い制度ページがチャンク数で上位を独占し、
    「補助金は何がある？」に対して1制度の断片だけが並ぶ。
  - グループ内の最高スコアのチャンクが説明として最適とは限らない（数表や注意書きが
    最上位になる）ため、グループ内の複数チャンクをまとめてLLMに渡して合成させる。
  - URLはLLMに書かせず、payloadから機械的に出力する（URL幻覚の防止）。
  - 議事録/所信表明側は鮮度にラグがあるため「現在議論中」と断言せず、
    会期名（令和8年第1回定例会 等）を明示する。
"""
import json
import os
from pathlib import Path

import boto3
import numpy as np

REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "cohere.embed-multilingual-v3")
LLM_MODEL = os.environ.get("LLM_MODEL", "jp.anthropic.claude-haiku-4-5-20251001-v1:0")
# 埋め込み済みインデックス（scripts/build_index.py が生成）。
# この規模（106チャンク）ではベクトルDBを立てるより同梱ファイルの方が安く速い。
INDEX_DIR = Path(os.environ.get(
    "INDEX_DIR", Path(__file__).resolve().parent / "data" / "index"))

bedrock = boto3.client("bedrock-runtime", region_name=REGION)

_index = None


def load_index():
    """(vectors, chunks) を返す。初回のみ読み込み、以後は使い回す。"""
    global _index
    if _index is None:
        vectors = np.load(INDEX_DIR / "vectors.npy")
        chunks = json.loads((INDEX_DIR / "chunks.json").read_text(encoding="utf-8"))
        _index = (vectors, chunks)
    return _index


# --------------------------------------------------------------------------
# 検索
# --------------------------------------------------------------------------
def embed_query(text):
    body = json.dumps({"texts": [text], "input_type": "search_query",
                       "truncate": "END"})
    resp = bedrock.invoke_model(modelId=EMBED_MODEL,
                                contentType="application/json",
                                accept="application/json", body=body)
    return json.loads(resp["body"].read())["embeddings"][0]


class _Hit:
    """Qdrant の ScoredPoint 互換（下流は payload / score しか使わない）。"""

    __slots__ = ("payload", "score")

    def __init__(self, payload, score):
        self.payload = payload
        self.score = score


class _Group:
    """Qdrant の PointGroup 互換（下流は hits しか使わない）。"""

    __slots__ = ("hits",)

    def __init__(self, hits):
        self.hits = hits


def retrieve(query, source_type=None, limit=5, group_size=3):
    """source_type で絞り、doc_id ごとにグループ化して検索する。

    Qdrant の query_points_groups(group_by="doc_id") と同じ挙動をメモリ内で行う。
    グループ化しないと、チャンク数の多い長い制度ページが上位を独占してしまう。
    """
    vectors, chunks = load_index()

    q = np.array(embed_query(query), dtype=np.float32)
    q /= max(float(np.linalg.norm(q)), 1e-12)
    scores = vectors @ q  # 保存時にL2正規化済みなので内積＝コサイン類似度

    by_doc = {}
    for i, c in enumerate(chunks):
        if source_type and c["source_type"] != source_type:
            continue
        by_doc.setdefault(c["doc_id"], []).append((float(scores[i]), i))

    # グループの代表スコア（グループ内の最高値）で上位 limit 件を選ぶ
    ranked = sorted(by_doc.values(),
                    key=lambda items: max(s for s, _ in items),
                    reverse=True)[:limit]

    groups = []
    for items in ranked:
        items.sort(key=lambda t: t[0], reverse=True)
        groups.append(_Group([_Hit(chunks[i], s) for s, i in items[:group_size]]))
    return groups


# --------------------------------------------------------------------------
# コンテキスト整形
# --------------------------------------------------------------------------
def _group_to_source(group, tag):
    """グループ→ LLMに渡す1ソース。chunk_index順に並べ直して文脈を復元する。"""
    hits = sorted(group.hits, key=lambda h: h.payload.get("chunk_index", 0))
    p = hits[0].payload
    body = "\n".join(h.payload["text"] for h in hits)
    return {
        "tag": tag,
        "title": p["title"],
        "url": p["url"],
        "body": body,
        "updated": p.get("updated", ""),
        "planned_time": p.get("planned_time", ""),
        "session": p.get("session", ""),
        "source": p.get("source", ""),
        "source_type": p["source_type"],
        "score": hits[0].score,
    }


def build_sources(seido_groups, giron_groups):
    sources = []
    for i, g in enumerate(seido_groups, 1):
        sources.append(_group_to_source(g, f"S{i}"))
    for i, g in enumerate(giron_groups, 1):
        sources.append(_group_to_source(g, f"G{i}"))
    return sources


def _render_context(sources):
    lines = []
    for s in sources:
        if s["source_type"] == "seido":
            meta = f"ページ更新日: {s['updated'] or '不明'}"
        else:
            when = s["planned_time"] or "時期の記載なし"
            meta = (f"発言の出どころ: {s['source'] or s['session'] or '不明'}"
                    f" / 実施予定: {when}")
        lines.append(f"[{s['tag']}] {s['title']}（{meta}）\n{s['body']}\n")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# 回答生成
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """あなたは東京都港区の子育て支援について、子育て中の保護者にわかりやすく案内する相談員です。
「いま使える支援」は港区の公式サイト、「これからの支援」は**区議会で語られた内容**が情報源です。
専門用語や行政特有の言い回しは避け、日常の言葉で説明してください。

厳守事項:
- 回答は必ず「参考情報」に書かれている内容のみに基づくこと。書かれていないことは絶対に補わない。
- 金額・対象年齢・条件は参考情報の記載どおりに書く。推測で数字を作らない。
- 各項目の末尾に、根拠となるタグを [S1] [G2] のように必ず付ける。
- URLは書かない（別途システムが付与する）。
- 「現在議論中」「今まさに検討中」と断言しない。議会の情報は公開までにラグがあるため、
  「令和8年第1回定例会で述べられた方針」のように、いつの情報かがわかる書き方をする。
- 参考情報に該当がない場合は、無いと正直に述べる。

出力フォーマット（Markdown、この2セクション構成を厳守）:

## いま使える支援
（[S...] の情報のみを使用。すでに申請・利用できる制度を、名称・対象・内容の順に箇条書き）

## 区議会で語られた、これからの支援
（[G...] の情報のみを使用。各項目で「どの会議で、誰が述べたか」に触れること。
　例:「令和8年第1回定例会の区長所信表明で述べられました」
　参考情報の「発言の出どころ」だけを根拠にし、書かれていない発言者を推測しない）
"""

USER_TEMPLATE = """区民からの質問:
{question}

参考情報:
{context}

上記の参考情報のみに基づいて、指定のフォーマットで回答してください。"""


def generate_answer(question, sources, conversation_history=""):
    context = _render_context(sources)
    user = USER_TEMPLATE.format(question=question, context=context)
    if conversation_history:
        user = f"これまでの会話:\n{conversation_history}\n\n{user}"

    resp = bedrock.converse(
        modelId=LLM_MODEL,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": 1500, "temperature": 0.2},
    )
    return resp["output"]["message"]["content"][0]["text"].strip()


def render_sources_section(sources):
    """出典はLLMに書かせず機械的に出す（URL幻覚の防止）。"""
    seido = [s for s in sources if s["source_type"] == "seido"]
    giron = [s for s in sources if s["source_type"] == "giron"]
    lines = ["", "---", "", "### 出典"]
    if seido:
        lines.append("")
        lines.append("**いま使える支援について（港区の公式サイト）**")
        for s in seido:
            d = f"（ページ更新日: {s['updated']}）" if s["updated"] else ""
            lines.append(f"- [{s['tag']}] [{s['title']}]({s['url']}){d}")
    if giron:
        lines.append("")
        lines.append("**これからの支援について（区議会での発言）**")
        # 同じ発言（所信表明など）から複数の施策が出るため、出どころは見出しにまとめる
        by_source = {}
        for s in giron:
            key = s["source"] or s["session"] or "出どころ不明"
            by_source.setdefault(key, []).append(s)
        for src, items in by_source.items():
            lines.append("")
            lines.append(f"*{src}* より")
            for s in items:
                when = f"（実施予定: {s['planned_time']}）" if s["planned_time"] else ""
                lines.append(f"- [{s['tag']}] [{s['title']}]({s['url']}){when}")
    lines += [
        "",
        "> 「区議会で語られた、これからの支援」は、その発言があった時点の内容です。"
        "議会の記録が公開されるまでには数か月かかるため、その後に変更されている場合があります。"
        "最新の状況は港区の窓口でご確認ください。",
    ]
    return "\n".join(lines)


def answer(question, conversation_history="", limit=5):
    """質問 → 2段構えのMarkdown回答（Ex-Appの本体処理）。"""
    seido_groups = retrieve(question, "seido", limit=limit)
    giron_groups = retrieve(question, "giron", limit=limit)
    sources = build_sources(seido_groups, giron_groups)
    if not sources:
        return ("## 回答\n\nご質問に関係する情報が見つかりませんでした。\n\n"
                "このサンプルが扱っているのは**港区の子育て支援**（手当・助成・保育・学童など）です。"
                "言葉を変えてもう一度お試しください。")
    body = generate_answer(question, sources, conversation_history)
    return body + "\n" + render_sources_section(sources)
