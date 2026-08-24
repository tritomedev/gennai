"""
保育所申請書チェックのコア。

方針（usecase-hoikusho-check.md の設計）:
  ① 申込書の画像（OCR）＋自由テキスト＋フォームの選択値 を構造化データに集約
     - 画像・テキストはLLMで抽出、フォームの選択値は人の明示入力なのでLLM結果を上書き
  ② Pythonのルールエンジンで決定的に判定（不足書類・記入漏れ・指数の目安）
     → 指数計算はLLMにさせない（算数ミス防止）
  ③ Pythonでテンプレ整形（幻覚防止）。冒頭に必ず免責を出す。
"""
import json
import re

import llm
import rules

MAX_IMAGES = 5  # 1リクエストでOCRする枚数の上限（申込書＋添付書類を想定）

EXTRACT_SYSTEM = """あなたは保育所の申込内容を構造化する抽出器です。
入力（申込書の画像・自由記述）から、以下のJSONスキーマに従って事実のみを抽出してください。
書かれていない項目は null にし、推測で埋めないこと。JSONのみを出力し、説明文は書かないこと。

スキーマ:
{
  "parents": [
    {"role": "父|母|保護者", "jiyu": "就労|自営|出産|疾病|障害|介護|求職|就学|災害|null",
     "work_days_per_month": 数値かnull, "work_hours_per_day": 数値かnull, "is_naitei": true/false/null}
  ],
  "hitorioya": true/false/null,
  "kyodai_doen": true/false/null,        // きょうだいが同じ園に同時申込 or 在園園へ新規申込
  "tashji": true/false/null,             // 多胎児
  "ku_gai_zaiju_ku_nai_tsukin": true/false/null,  // 区外在住で区内通勤
  "seikatsu_hogo": true/false/null,
  "hoikushi_naitei": true/false/null,    // 保育士・看護師内定
  "taino_3month": true/false/null,       // 保育料3か月以上滞納
  "child_shogai": true/false/null,       // 申込児または同居児に障害
  "prepared_docs": ["用意した／提出済みと述べている書類名の配列。未提出・未取得と述べている書類は含めないこと。保護者ごとの書類は「父の就労証明書」のように役割を付けること"],
  "kibo_code_ok": true/false/null,       // 希望園を保育園コードで記入している
  "jiyu_single_ok": true/false/null,     // 事由を父母それぞれ1つに絞っている
  "signed_ok": true/false/null,          // 確認書に父母とも署名
  "shurou_date_ok": true/false/null,     // 就労証明書の発行日が3か月以内
  "no_blank_ok": true/false/null         // 空欄がない
}"""

IMAGE_INSTRUCTION = (
    "添付された画像は保育所の申込書・添付書類です。記載内容を読み取り、"
    "システム指示のスキーマに従ってJSONを抽出してください。"
    "空欄・未記入・未チェックの項目は該当フラグを false または null にすること。"
    "読み取れない項目は null にし、推測で埋めないこと。"
    "\n\n複数の画像がある場合、画像1枚1枚がそれぞれ提出された書類です。"
    "申込書の「添付書類」欄に書かれた書類名だけでなく、"
    "**画像そのものとして提出されている書類も prepared_docs に必ず含めてください**。"
    "（例: 母の就労証明書の画像が添付されていれば、申込書の記載に無くても"
    "prepared_docs に「母の就労証明書」を含める）"
    "書類が誰の分かは、その書類に書かれた続柄（父・母）から判断すること。"
)


def _parse_json(raw):
    raw = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", raw, re.S)
    return json.loads(m.group(0)) if m else {}


def extract(application_text):
    """申込内容テキスト → 構造化dict。"""
    content = [{"text": f"申込内容:\n{application_text}\n\n上記からJSONを抽出してください。"}]
    return _parse_json(llm.converse_with_fallback(EXTRACT_SYSTEM, content))


def extract_from_images(images, extra_text=""):
    """申込書の画像（スマホ写真等）をClaudeビジョンで読み取り → 構造化dict。

    images: [(bytes, "png"|"jpeg"|...), ...]  最大 MAX_IMAGES 枚。
    extra_text: 画像の補足として利用者が書いた自由記述（あれば併せて渡す）。
    """
    content = [
        {"image": {"format": fmt, "source": {"bytes": data}}}
        for data, fmt in images[:MAX_IMAGES]
    ]
    text = IMAGE_INSTRUCTION
    if extra_text.strip():
        text += f"\n\n利用者による補足（画像の内容と矛盾する場合は補足を優先）:\n{extra_text.strip()}"
    content.append({"text": text})
    return _parse_json(llm.converse(EXTRACT_SYSTEM, content))  # 画像はClaudeのみ


# --------------------------------------------------------------------------
# フォーム入力のマージ（人の明示入力はLLMの抽出結果より優先）
# --------------------------------------------------------------------------
def apply_form(data, form):
    """源内Webのフォーム選択値を抽出結果に反映する。

    form: {"jukyo": str, "setai": [value], "prepared_docs": [書類名]}
    """
    data = dict(data or {})

    jukyo = (form.get("jukyo") or "").strip()
    if jukyo:
        data["ku_gai_zaiju_ku_nai_tsukin"] = jukyo == "ku_gai_tsukin"
        data["ku_gai_zaiju"] = jukyo in ("ku_gai_tsukin", "ku_gai")
        data["tennyu_yotei"] = jukyo == "tennyu"

    setai = form.get("setai")
    if setai:  # チェックボックスは「チェックしたものだけ True」。未チェックは false 扱い
        for value, key in rules.SETAI_FLAGS.items():
            data[key] = value in setai

    docs = form.get("prepared_docs")
    if docs:
        # フォームで「父の就労証明書」と保護者を指定した書類については、
        # 抽出結果の役割なし（「就労証明書」だけ）の記述を捨てる。
        # 残すと「どちらの分か不明＝暫定OK」判定になり、不足を見逃すため。
        merged = [d for d in (data.get("prepared_docs") or []) if not _superseded(d, docs)]
        for d in docs:
            if d not in merged:
                merged.append(d)
        data["prepared_docs"] = merged

    return data


def _superseded(doc, form_docs):
    """抽出された書類名 doc が、フォームの役割付き指定に取って代わられるか。"""
    if "父" in doc or "母" in doc:
        return False
    for fd in form_docs:
        if "父" not in fd and "母" not in fd:
            continue
        core = fd.replace("父の", "").replace("母の", "")
        if core and core in doc:
            return True
    return False


# --------------------------------------------------------------------------
# ルールエンジン（決定的）
# --------------------------------------------------------------------------
def _kw_for(required):
    """必要書類名 → 照合キーワードのリスト（該当ルールなしなら None）。

    「本人確認書類」に「確認書」が含まれるように断片同士が包含関係になるため、
    一致した断片のうち最も長いものを採用する（先勝ちだと誤判定する）。
    """
    best = None
    for frag, kws in rules.DOC_KEYWORDS.items():
        if frag in required and (best is None or len(frag) > len(best[0])):
            best = (frag, kws)
    return best[1] if best else None


def _doc_prepared(required, prepared):
    """全世帯共通書類が用意されているか（保護者の区別なし）。"""
    joined = " ".join(p or "" for p in prepared)
    if not joined:
        return False
    kws = _kw_for(required)
    if kws is not None:
        return any(kw in joined for kw in kws)
    return required[:3] in joined  # フォールバック


def _doc_prepared_for_role(required, role, prepared):
    """保護者ごとに必要な書類（就労証明書等）が、その保護者の分として用意されているか。

    - 「父の就労証明書」のように役割が明記されていれば役割一致で判定。
    - 「就労証明書」のように役割の記載が無ければ、どちらの分か不明なので暫定で用意済み扱い。
    """
    kws = _kw_for(required) or [required[:3]]
    for p in prepared:
        p = p or ""
        if any(kw in p for kw in kws):
            if role and role in p:
                return True
            if "父" not in p and "母" not in p:
                return True  # 役割の記載なし＝暫定OK
    return False


def run_checks(data):
    prepared = data.get("prepared_docs") or []
    parents = data.get("parents") or []

    # --- 必要書類 ---
    # 共通（世帯で1通）
    common = list(rules.COMMON_DOCS)
    if data.get("hitorioya"):
        common.append(rules.CONDITIONAL_DOCS["ひとり親"])
    if data.get("hoikushi_naitei"):
        common.append(rules.CONDITIONAL_DOCS["保育士看護師内定"])
    if data.get("tennyu_yotei"):
        common.append(rules.CONDITIONAL_DOCS["転入予定"])
    seen, common_unique = set(), []
    for d in common:
        if d not in seen:
            seen.add(d)
            common_unique.append(d)

    # 保育を必要とする事由の証明は保護者ごとに必要
    per_parent = []  # (role, doc)
    for p in parents:
        jiyu = p.get("jiyu")
        role = p.get("role") or "保護者"
        for doc in rules.JIYU_DOCS.get(jiyu, []):
            per_parent.append((role, doc))

    missing_docs = [d for d in common_unique if not _doc_prepared(d, prepared)]
    for role, doc in per_parent:
        if not _doc_prepared_for_role(doc, role, prepared):
            missing_docs.append(f"{doc}（{role}の分）")

    required_unique = common_unique + [f"{doc}（{role}の分）" for role, doc in per_parent]

    # --- 記入漏れ ---
    kinyu_issues = []
    for label, key in rules.KINYU_CHECK_ITEMS:
        val = data.get(key)
        if val is False:
            kinyu_issues.append(label)

    # --- 指数の目安 ---
    def base_for(p):
        jiyu = p.get("jiyu")
        if jiyu in ("就労", "自営", "介護", "就学"):
            d = p.get("work_days_per_month") or 0
            h = p.get("work_hours_per_day") or 0
            return rules.kijun_shisu_work(d, h, bool(p.get("is_naitei")))
        return rules.KIJUN_SHISU_OTHER.get(jiyu, 0)

    base_total = sum(base_for(p) for p in parents)
    if data.get("hitorioya"):
        base_total += rules.HITORIOYA_BONUS

    chosei = 0
    chosei_detail = []
    flag_map = {
        "seikatsu_hogo": "生活保護",
        "child_shogai": "申込児または同居児に障害",
        "kyodai_doen": "きょうだい同園同時申込または在園園へ新規申込",
        "tashji": "多胎児",
        "hoikushi_naitei": "保育士・看護師内定（1年以上）",
        "ku_gai_zaiju_ku_nai_tsukin": "区外在住で区内通勤",
        "taino_3month": "保育料を3か月以上滞納",
    }
    for key, name in flag_map.items():
        if data.get(key):
            pts = rules.CHOSEI_SHISU[name]
            chosei += pts
            chosei_detail.append((name, pts))

    shisu_total = base_total + chosei

    # --- 要件の警告 ---
    warnings = []
    for p in parents:
        if p.get("jiyu") in ("就労", "自営"):
            d = p.get("work_days_per_month")
            h = p.get("work_hours_per_day")
            if d and h and d * h < rules.WORK_MIN_HOURS_PER_MONTH:
                warnings.append(
                    f"{p.get('role', '保護者')}の就労が月{d*h:.0f}時間で、"
                    "認定の最低ライン（月48時間以上）を下回る可能性があります。"
                )
        if p.get("jiyu") == "求職":
            warnings.append(
                "求職事由は認定期間が短く（原則3か月）、期間内に就労証明書の提出がないと退園になります。"
            )
    if data.get("ku_gai_zaiju_ku_nai_tsukin"):
        warnings.append("区外在住で区内通勤のため、調整指数が−9されます。")
    elif data.get("ku_gai_zaiju"):
        warnings.append(
            "港区外在住で通勤先も区外の場合、港区の認可保育所の申込みは"
            "受け付けられない可能性があります。お住まいの区市町村にご確認ください。"
        )
    if data.get("tennyu_yotei"):
        warnings.append(
            "転入予定の場合は、賃貸／売買契約書と同意書等の提出が必要です。"
            "入園までに港区に住民登録がされているか確認してください。"
        )
    if data.get("taino_3month"):
        warnings.append("保育料の3か月以上の滞納があると−20の大きな減点になります。")
    if not parents:
        warnings.append(
            "保育を必要とする事由（就労・出産・疾病等）が読み取れませんでした。"
            "父母それぞれの事由と就労状況を入力すると、指数の目安まで確認できます。"
        )

    return {
        "missing_docs": missing_docs,
        "required_docs": required_unique,
        "kinyu_issues": kinyu_issues,
        "base_total": base_total,
        "chosei": chosei,
        "chosei_detail": chosei_detail,
        "shisu_total": shisu_total,
        "shisu_available": bool(parents),  # 事由が取れていなければ指数は出さない
        "warnings": warnings,
    }


# --------------------------------------------------------------------------
# 整形（テンプレ・決定的）
# --------------------------------------------------------------------------
JUKYO_LABEL = {
    "ku_nai": "港区内在住",
    "ku_gai_tsukin": "港区外在住・港区内通勤",
    "ku_gai": "港区外在住・通勤先も区外",
    "tennyu": "港区へ転入予定",
}
SETAI_LABEL = dict((v, t) for t, v in rules.SETAI_ITEMS)


def summarize(data, form):
    """読み取り・入力の結果を利用者が確認できる箇条書きにする。"""
    lines = []
    for p in data.get("parents") or []:
        role = p.get("role") or "保護者"
        parts = [p.get("jiyu") or "事由が読み取れませんでした"]
        d, h = p.get("work_days_per_month"), p.get("work_hours_per_day")
        if d or h:
            parts.append(f"月{d or '?'}日・1日{h or '?'}時間")
        if p.get("is_naitei"):
            parts.append("就労内定")
        lines.append(f"{role}：{' / '.join(str(x) for x in parts)}")

    jukyo = (form.get("jukyo") or "").strip()
    if jukyo in JUKYO_LABEL:
        lines.append(f"住まい・通勤：{JUKYO_LABEL[jukyo]}")
    elif data.get("ku_gai_zaiju_ku_nai_tsukin"):
        lines.append(f"住まい・通勤：{JUKYO_LABEL['ku_gai_tsukin']}")
    elif data.get("ku_gai_zaiju"):
        lines.append(f"住まい・通勤：{JUKYO_LABEL['ku_gai']}")
    elif data.get("tennyu_yotei"):
        lines.append(f"住まい・通勤：{JUKYO_LABEL['tennyu']}")

    setai_on = [SETAI_LABEL[v] for v, k in rules.SETAI_FLAGS.items()
                if data.get(k) and v in SETAI_LABEL]
    if setai_on:
        lines.append("世帯の状況：" + "／".join(setai_on))

    docs = data.get("prepared_docs") or []
    if docs:
        lines.append("用意した書類：" + "、".join(str(d) for d in docs))
    return lines


def render(findings, data=None, form=None):
    md = ["## 保育所申込チェック結果", "", f"> {rules.DISCLAIMER}", ""]

    # ① 読み取り・入力内容の確認
    summary = summarize(data or {}, form or {})
    if summary:
        md.append("## ① 読み取った内容（確認してください）")
        md += [f"- {s}" for s in summary]
        md.append("")
        md.append("※ 画像から読み取った内容が実際と違う場合は、フォームで補って再チェックしてください。")
        md.append("")

    # ② 不備・要確認
    md.append("## ② 不備・要確認")
    issues = False
    if findings["missing_docs"]:
        issues = True
        md.append("**不足している可能性のある書類**")
        md += [f"- {d}" for d in findings["missing_docs"]]
        md.append("")
    if findings["kinyu_issues"]:
        issues = True
        md.append("**記入・確認のポイント**")
        md += [f"- {x}" for x in findings["kinyu_issues"]]
        md.append("")
    if findings["warnings"]:
        issues = True
        md.append("**要件に関する注意**")
        md += [f"- ⚠️ {w}" for w in findings["warnings"]]
        md.append("")
    if not issues:
        md.append("入力内容からは、目立った不備は見つかりませんでした（※あくまで参考です）。")
        md.append("")

    # ③ 指数の目安
    md.append("## ③ 利用調整指数の目安（参考）")
    if not findings.get("shisu_available"):
        md.append(
            "保育を必要とする事由（就労・出産・疾病など）が読み取れなかったため、指数は算出していません。"
            "父母それぞれの事由と就労日数・時間がわかる画像を追加するか、補足欄に入力してください。"
        )
        return "\n".join(md)
    md.append(f"- 基準指数の合計（父母）：**約 {findings['base_total']}**")
    if findings["chosei_detail"]:
        md.append("- 調整指数：")
        for name, pts in findings["chosei_detail"]:
            sign = f"+{pts}" if pts >= 0 else str(pts)
            md.append(f"    - {name}：{sign}")
    md.append(f"- **合計の目安：約 {findings['shisu_total']}**")
    md.append("")
    md.append(
        "※ この指数は簡略化した代表値による**目安**です。実際の指数・優先順位・内定可否は"
        "港区の窓口で確認してください。選考は先着順ではなく利用調整で行われます。"
    )
    return "\n".join(md)


def check(text="", images=None, form=None):
    """画像・自由テキスト・フォームからチェック結果Markdownを作る（Ex-Appの本体処理）。

    text:   自由記述（申込内容の補足）
    images: [(bytes, fmt), ...] 申込書・添付書類の画像
    form:   {"jukyo": str, "setai": [value], "prepared_docs": [書類名]}
    """
    text = (text or "").strip()
    images = images or []
    form = form or {}

    if images:
        data = extract_from_images(images, text)
    elif text:
        data = extract(text)
    else:
        data = {}  # フォームの選択値のみでもチェックはできる

    data = apply_form(data, form)
    return render(run_checks(data), data, form)
