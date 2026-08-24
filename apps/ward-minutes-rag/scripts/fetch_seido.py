#!/usr/bin/env python3
"""
港区 子育て・補助金 制度ページ（AsIs＝現行制度）をサンプルデータ化する。

方針:
  - 静的HTML・UTF-8の素直なCMS（tmp_接頭辞）。セッション不要。
  - 本文コンテナ #tmp_contents 内のテキストを抽出し、
    おすすめ枠(tmp_reccommend*)・右ナビ(tmp_rnavi)・検索ウィジェット(cogmo)・
    script/style を除外する。
  - 出力は data/sample/seido.jsonl（1制度=1レコード）。

使い方:
  python3 scripts/fetch_seido.py
"""
import json
import re
import sys
import time
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://www.city.minato.tokyo.jp"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

APP = Path(__file__).resolve().parent.parent
URLS_TSV = APP / "data" / "raw" / "urls.tsv"
OUT = APP / "data" / "sample" / "seido.jsonl"

SKIP_ID_PREFIX = ("tmp_reccommend", "tmp_rnavi", "tmp_sma", "cogmo", "otowidget",
                  "tmp_pankuzu", "tmp_wrap_custom_update")
SKIP_CLASS_FRAG = ("cogmo", "rnavi", "sma_search", "search_keywords")
VOID_TAGS = {"br", "img", "input", "meta", "hr", "link", "area", "base", "col"}
BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "tr", "div", "dt", "dd"}


class MainExtractor(HTMLParser):
    """#tmp_contents の中身だけをテキスト抽出する（スキップ枠は深さで除外）。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []            # [(tag, is_skip_root)] 開いている非void要素
        self.capture_depth = None  # tmp_contents を開いた時点の stack 長
        self.skip_from = None      # スキップ開始時の stack 長（それ以深はスキップ）
        self.noise = 0             # script/style/noscript 内
        self.parts = []

    @property
    def capturing(self):
        return self.capture_depth is not None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.noise += 1
            return
        if tag in VOID_TAGS:
            if self.capturing and self.skip_from is None and self.noise == 0 and tag == "br":
                self.parts.append("\n")
            return

        d = dict(attrs)
        _id = d.get("id", "")
        _cls = d.get("class", "")

        if _id == "tmp_contents" and self.capture_depth is None:
            self.capture_depth = len(self.stack)

        is_skip = self.capturing and self.skip_from is None and (
            any(_id.startswith(p) for p in SKIP_ID_PREFIX)
            or any(f in _cls for f in SKIP_CLASS_FRAG))
        if is_skip:
            self.skip_from = len(self.stack)

        self.stack.append(tag)

        if (tag in BLOCK_TAGS and self.capturing
                and self.skip_from is None and self.noise == 0):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.noise = max(0, self.noise - 1)
            return
        if tag in VOID_TAGS:
            return
        # 対応する開始タグまで巻き戻す（不整合HTMLに耐える）
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] == tag:
                del self.stack[i:]
                break
        if self.skip_from is not None and len(self.stack) <= self.skip_from:
            self.skip_from = None
        if self.capture_depth is not None and len(self.stack) < self.capture_depth:
            self.capture_depth = None  # tmp_contents を閉じた

    def handle_data(self, data):
        if self.capturing and self.skip_from is None and self.noise == 0:
            self.parts.append(data)

    def text(self):
        raw = "".join(self.parts)
        lines = [re.sub(r"[ \t　]+", " ", ln).strip() for ln in raw.splitlines()]
        lines = [ln for ln in lines if ln]
        return "\n".join(lines)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def extract_title(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if m:
        return strip_tags(m.group(1))
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return strip_tags(m.group(1)) if m else ""


def extract_update(html):
    m = re.search(r'id="tmp_update"[^>]*>(.*?)</div>', html, re.S)
    seg = m.group(1) if m else html[:4000]
    m2 = re.search(r"(\d{4})[年/.\-](\d{1,2})[月/.\-](\d{1,2})", strip_tags(seg))
    if m2:
        return f"{int(m2.group(1)):04d}-{int(m2.group(2)):02d}-{int(m2.group(3)):02d}"
    return ""


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def main():
    rows = []
    for line in URLS_TSV.read_text(encoding="utf-8").splitlines():
        if line.strip():
            name, slug, path = line.split("\t")
            rows.append((name, slug, path))

    today = date.today().isoformat()
    records = []
    for name, slug, path in rows:
        url = BASE + path
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[SKIP] {name}: {e}", file=sys.stderr)
            continue
        p = MainExtractor()
        p.feed(html)
        body = p.text()
        rec = {
            "id": f"seido-{slug}",
            "source_type": "seido",
            "title": extract_title(html) or name,
            "seido_name": name,
            "text": body,
            "url": url,
            "updated": extract_update(html),
            "fetched_at": today,
            "ward": "港区",
        }
        records.append(rec)
        print(f"[OK] {name}: len={len(body)} updated={rec['updated'] or '-'}")
        time.sleep(1.0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"\n=> {len(records)} 件を {OUT} に書き出し")


if __name__ == "__main__":
    main()
