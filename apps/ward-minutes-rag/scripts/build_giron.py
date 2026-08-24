#!/usr/bin/env python3
"""
港区「議論中・今後の方針」データ（未来側）をサンプル化する。

出典:
  令和8年第1回港区議会定例会 区長所信表明「重点的に取り組む5つの施策」
  https://www.city.minato.tokyo.jp/kikaku/kuse/gaiyo/kucho/aisatsu/r08-1shoshin/02.html
  ※議事録ASP（gikai2, セッション駆動）の攻略はPOCでは行わない方針のため、
    議会で区長が述べた所信表明（＝今後の方針が集約された公開ページ）を
    「議論中/今後」側の実データとして手作業抜粋した。引用は原文表現。

これは自動スクレイピングではなく手キュレーション。将来的に議事録本文の
逐語データへ差し替える（[TASK] 議事録ASPセッション攻略）。

使い方:
  python3 scripts/build_giron.py
"""
import json
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
OUT = APP / "data" / "sample" / "giron.jsonl"

SOURCE = "令和8年第1回港区議会定例会 区長所信表明（重点的に取り組む5つの施策）"
URL = "https://www.city.minato.tokyo.jp/kikaku/kuse/gaiyo/kucho/aisatsu/r08-1shoshin/02.html"
SESSION_DATE = "2026-02"  # 令和8年第1回定例会（会期は2026年2〜3月）

ITEMS = [
    ("sango-kenshin", "産後初期段階の女性健康診査費用助成",
     "産前産後の女性の心と身体を支えるために、これまでの妊婦健診に加え、新たに産後初期段階の女性の健康診査の費用助成を開始する。", ""),
    ("kosodate-program", "孤立させない子育てプログラム",
     "妊娠期から子どもが思春期になるまで参加できるプログラムを通じて、保護者が子どもとの関係づくりに自信を持って向き合えるよう支援する。", ""),
    ("boshi-shortcare", "母子一体型ショートケア事業",
     "母子生活支援施設を活用し、親子関係の修復や再構築の支援を強化し、虐待を未然に防止する。", ""),
    ("innovation-lab", "港区イノベーションラボ",
     "子どもが区政に主体的に参加し、政策提案を行う事業を進める。", ""),
    ("dare-demo-tsuen", "港区版「こども誰でも通園制度」本格実施",
     "在宅子育て世帯の孤立防止に向け、対象年齢を国基準より広く設定し、月24時間まで利用可能・利用料無料で本格実施する。", "令和8年度から"),
    ("youchien-azukari", "区立幼稚園の預かり保育時間拡大",
     "朝と夕方の預かり保育時間を6園で拡大し、夏季等休業中の一時預かり事業を全園に拡大する。", "来年度から"),
    ("ichiji-coupon", "一時保育料の電子クーポン無償化",
     "一時保育や一時預かりの保育料と利用料について、電子クーポンを活用し、子ども一人当たり年間144時間までを無償化する。", ""),
    ("byoji-hoiku", "病児保育室の定員拡大",
     "病児保育室サニーガーデンこどもケアルームの定員を8名から12名に拡大する。", "来年度"),
    ("kaji-shien", "家事支援サービスの対象年齢拡大",
     "現在は妊娠中から2歳までが対象の家事支援サービスについて、対象年齢を小学校1年生までに都内で初めて拡大する。", ""),
    ("morning-school", "モーニングスクール全校展開",
     "全ての区立小学校の学校図書館でモーニングスクールを実施し、学校図書館スタッフを配置して読み聞かせや本の紹介などを行う。", "来年度から"),
    ("houkago-club", "放課GO→クラブの定員増",
     "放課GO→クラブの定員を全体で133人増やす。", "来年度"),
    ("minsetsu-gakudo", "民設学童クラブの整備補助",
     "区内に学童クラブを開設する民間事業者に対し、補助率10分の10の整備費や運営費等補助を新たに開始する。", ""),
    ("kougai-gakushu", "校外学習等費用の無償化",
     "学用品無償化に加え、校外学習や移動教室、夏季学園にかかる負担もなくす。", "来年度"),
]


def main():
    records = []
    for slug, title, text, planned in ITEMS:
        records.append({
            "id": f"giron-{slug}",
            "source_type": "giron",           # 議論中/今後の方針（未来側）
            "title": title,
            "text": text,
            "planned_time": planned,
            "source": SOURCE,
            "session": "令和8年第1回定例会",
            "session_date": SESSION_DATE,
            "url": URL,
            "curation": "manual",             # 手キュレーション（自動収集ではない）
            "ward": "港区",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"=> {len(records)} 件を {OUT} に書き出し")


if __name__ == "__main__":
    main()
