"""
港区 保育所申請書チェック Ex-App（源内プロトコル準拠）— TASK-038 / TASK-039

2つのモードを1つのExAppで提供する:
  - 相談モード ... `message`（自由入力）＋ `conversation_history` でAIと会話しながら手続きを進める
  - チェックモード ... 申込書の画像（OCR）＋補足フォームで、不備・必要書類・指数の目安を判定する
  画像またはチェック用フォームのいずれかが入力されていればチェックモード、そうでなければ相談モード。

源内プロトコル:
  POST /  で {"inputs": {...}} を受け、{"outputs": "Markdown"} を返す。
  源内Webに登録するリクエスト定義JSONは GET /schema がそのまま返す。

起動:
  <venv>/bin/uvicorn main:app --host 0.0.0.0 --port 8002
"""
import base64
import binascii
import hmac
import json
import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

import chat
import check
import llm
import rules

# 源内fileコンポーネント／UIから来る画像を Claude ビジョンで扱える形式に対応付け
IMAGE_FORMATS = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "gif": "gif"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hoikusho-check")

app = FastAPI(title="港区 保育所申請書チェック (hoikusho-check)")

# 公開ホスト前提。キーが設定されていれば x-api-key を検証する。
# Lambdaでは Secrets Manager のARNを EXAPP_API_KEY_SECRET_ARN で渡し、起動時に1回だけ取得する。
def _load_api_key():
    arn = os.environ.get("EXAPP_API_KEY_SECRET_ARN")
    if arn:
        try:
            import boto3
            return boto3.client("secretsmanager").get_secret_value(SecretId=arn)["SecretString"].strip()
        except Exception:
            logger.exception("APIキーの取得に失敗（認証を有効にできません）")
            return ""
    return os.environ.get("EXAPP_API_KEY", "")


EXAPP_API_KEY = _load_api_key()


# --------------------------------------------------------------------------
# 源内Webに登録するリクエスト定義（UIはこのJSONから自動生成される）
# --------------------------------------------------------------------------
def request_schema():
    return {
        "message": {
            "title": "AIと会話して業務を進める",
            "desc": "保育所の申込みについて相談したいことを入力してください"
                    "（例：就労証明書はいつ発行されたものが必要ですか？）。"
                    "申込書のチェックだけしたい場合は空のままで構いません。"
                    "\n※ このデモは全員が同じアカウントを共有します。実在の氏名・住所などの個人情報は入力しないでください。",
            "type": "textarea",
            "required": False,
        },
        "form_images": {
            "title": "申込書・添付書類の画像",
            "desc": f"申込書や就労証明書をスマホで撮った画像をアップロードするとOCRで読み取ります"
                    f"（jpg/png、最大{check.MAX_IMAGES}枚）。"
                    f"\n※ このデモは全員が同じアカウントを共有します。実在の氏名・住所などの個人情報は入力しないでください。",
            "type": "file",
            "required": False,
            # 既定は multiple=false（1枚のみ・追加すると上書き）。複数枚を受けるには明示が必要。
            "multiple": True,
            "max_file_count": check.MAX_IMAGES,
            "accept": "image/*",
            "max_size": "5MB",
        },
        "jukyo": {
            "title": "住まいと通勤",
            "desc": "港区内在住かどうかで調整指数が変わります。",
            "type": "select",
            "required": False,
            "items": [{"title": t, "value": v} for t, v in rules.JUKYO_ITEMS],
        },
        "setai": {
            "title": "世帯の状況（当てはまるものすべて）",
            "type": "checkbox",
            "required": False,
            "items": [{"title": t, "value": v} for t, v in rules.SETAI_ITEMS],
        },
        "prepared_docs": {
            "title": "用意した書類（当てはまるものすべて）",
            "type": "checkbox",
            "required": False,
            "items": [{"title": d, "value": d} for d in rules.PREPARED_DOC_ITEMS],
        },
        "conversation_history": {
            "title": "会話履歴",
            "type": "textarea",
            "required": False,
        },
    }


def _authorized(request: Request) -> bool:
    if not EXAPP_API_KEY:
        return True  # ローカル開発モード
    return hmac.compare_digest(request.headers.get("x-api-key", ""), EXAPP_API_KEY)


@app.get("/")
def health():
    return {"status": "ok", "app": "hoikusho-check", "llm": llm.LLM_MODEL}


@app.get("/schema")
def schema():
    """源内Webの「リクエスト形式」にそのまま貼り付けるJSON。"""
    return request_schema()


# --------------------------------------------------------------------------
# 入力パース
# --------------------------------------------------------------------------
def _images_from_files(files):
    """源内の inputs.files（[{key, files:[{filename, content(base64)}]}]）から画像を取り出す。"""
    images = []
    for group in files or []:
        for f in group.get("files", []):
            name = (f.get("filename") or "").lower()
            ext = name.rsplit(".", 1)[-1] if "." in name else ""
            fmt = IMAGE_FORMATS.get(ext)
            if not (fmt and f.get("content")):
                continue
            try:
                images.append((base64.b64decode(f["content"]), fmt))
            except (binascii.Error, ValueError):
                logger.warning("base64のデコードに失敗: %s", name)
    return images


def _multi(value):
    """checkbox の複数選択（"a,b" のカンマ区切り文字列）をリストにする。"""
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


UI_HTML = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>港区 保育所申込チェック（開発確認用）</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, -apple-system, "Hiragino Sans", sans-serif;
         max-width: 820px; margin: 0 auto; padding: 24px 16px 64px; line-height: 1.75; }
  h1 { font-size: 1.25rem; margin-bottom: 4px; }
  .note { color: #888; font-size: .8rem; }
  textarea, select { width: 100%; box-sizing: border-box; padding: 10px; font-size: 1rem;
             border: 1px solid #bbb; border-radius: 8px; font-family: inherit; }
  textarea { min-height: 120px; }
  button { margin-top: 10px; padding: 10px 22px; font-size: 1rem; border: 0;
           border-radius: 8px; background: #173e7c; color: #fff; cursor: pointer; }
  button:disabled { background: #999; }
  .tabs { display: flex; gap: 6px; margin: 16px 0; border-bottom: 1px solid #ccc; }
  .tabs button { margin: 0; border-radius: 8px 8px 0 0; background: #eee; color: #333; font-size: .9rem; }
  .tabs button.on { background: #173e7c; color: #fff; }
  .panel { display: none; }
  .panel.on { display: block; }
  fieldset { border: 1px solid #bbb; border-radius: 8px; margin: 14px 0; padding: 12px 14px; }
  legend { font-weight: bold; font-size: .9rem; padding: 0 6px; }
  fieldset label { display: block; font-size: .9rem; font-weight: normal; }
  .samples { margin: 10px 0; display: flex; flex-wrap: wrap; gap: 8px; }
  .samples button { background: #eee; color: #333; font-size: .8rem; padding: 6px 12px; margin: 0; }
  @media (prefers-color-scheme: dark) { .samples button, .tabs button { background:#333; color:#ddd; }
    .tabs button.on { background:#173e7c; color:#fff; } }
  #out { margin-top: 28px; border-top: 1px solid #ccc; padding-top: 20px; }
  #out h2 { font-size: 1.05rem; border-left: 4px solid #173e7c; padding-left: 10px; margin-top: 24px; }
  #out blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 12px; color: #888; font-size: .85rem; }
  .spin { color: #888; }
</style>
</head>
<body>
  <h1>港区 保育所申込チェック</h1>
  <div class="note">源内 Ex-App の開発確認用UI（本番の入口は源内Web側）。入力はダミーで。</div>

  <div class="tabs">
    <button id="tab-chat" class="on" onclick="tab('chat')">AIと会話して進める</button>
    <button id="tab-check" onclick="tab('check')">申込書をチェック</button>
  </div>

  <div id="panel-chat" class="panel on">
    <textarea id="msg" placeholder="例）就労証明書はいつ発行されたものが必要ですか？"></textarea>
    <div class="samples">
      <button onclick="setMsg(0)">就労証明書の発行日は？</button>
      <button onclick="setMsg(1)">求職中でも申し込める？</button>
      <button onclick="setMsg(2)">申込みの締切はいつ？</button>
    </div>
    <button id="go-chat" onclick="ask()">送信</button>
    <button onclick="resetChat()" style="background:#888;">会話をリセット</button>
    <div class="note" id="histnote"></div>
  </div>

  <div id="panel-check" class="panel">
    <fieldset>
      <legend>📷 申込書・添付書類の画像</legend>
      <input type="file" id="img" accept="image/*" multiple>
      <div class="note" style="margin-top:6px;">スマホ写真OK。複数枚選べます（申込書の各ページ・就労証明書など）。</div>
    </fieldset>
__FORM_FIELDS__
    <fieldset>
      <legend>補足（自由記述）</legend>
      <textarea id="note" placeholder="例）父：会社員 月20日・1日8時間。母：パート 月16日・1日5時間。" style="min-height:80px;"></textarea>
    </fieldset>
    <button id="go-check" onclick="runCheck()">チェックする</button>
  </div>

  <div id="out"></div>

<script>
const API_KEY = '__API_KEY__';
let history_ = '';

const MSGS = [
  '就労証明書はいつ発行されたものが必要ですか？',
  '今は求職中なのですが、申し込めますか？必要な書類も教えてください。',
  '令和8年4月入園の申込みの締切はいつですか？',
];
function setMsg(i){ document.getElementById('msg').value = MSGS[i]; }
function tab(name){
  for(const t of ['chat','check']){
    document.getElementById('panel-'+t).classList.toggle('on', t===name);
    document.getElementById('tab-'+t).classList.toggle('on', t===name);
  }
}
function resetChat(){ history_ = ''; document.getElementById('histnote').textContent = ''; }
function toBase64(file){
  return new Promise((res, rej)=>{
    const r = new FileReader();
    r.onload = ()=> res(r.result.split(',')[1]);
    r.onerror = rej;
    r.readAsDataURL(file);
  });
}
function checked(name){
  return [...document.querySelectorAll('input[name="'+name+'"]:checked')].map(e=>e.value).join(',');
}
async function post(inputs, waiting){
  const out = document.getElementById('out');
  out.innerHTML = '<p class="spin">' + waiting + '</p>';
  const t0 = performance.now();
  try{
    const r = await fetch('/', {
      method:'POST',
      headers:{'Content-Type':'application/json', 'x-api-key':API_KEY},
      body: JSON.stringify({inputs})
    });
    const d = await r.json();
    const sec = ((performance.now()-t0)/1000).toFixed(1);
    out.innerHTML = marked.parse(d.outputs || '(空の応答)') + '<p class="spin">応答 ' + sec + '秒</p>';
    return d.outputs || '';
  }catch(e){ out.innerHTML = '<p class="spin">エラー: ' + e + '</p>'; return ''; }
}
async function ask(){
  const msg = document.getElementById('msg').value.trim();
  if(!msg){ document.getElementById('out').innerHTML = '<p class="spin">相談内容を入力してね</p>'; return; }
  const go = document.getElementById('go-chat');
  go.disabled = true;
  const ans = await post({message: msg, conversation_history: history_}, '考え中…（数秒）');
  go.disabled = false;
  if(ans){
    history_ += (history_ ? '\\n\\n' : '') + 'ユーザー: ' + msg + '\\nAI: ' + ans;
    document.getElementById('msg').value = '';
    document.getElementById('histnote').textContent = '会話履歴 ' + history_.length + '文字を保持中（源内側の会話継続に相当）';
  }
}
async function runCheck(){
  const files = [...document.getElementById('img').files];
  const inputs = {
    message: document.getElementById('note').value.trim(),
    jukyo: document.getElementById('jukyo').value,
    setai: checked('setai'),
    prepared_docs: checked('prepared_docs'),
  };
  if(files.length){
    const encoded = await Promise.all(files.map(async f => ({filename: f.name, content: await toBase64(f)})));
    inputs.files = [{key:'form_images', files: encoded}];
  }
  if(!files.length && !inputs.jukyo && !inputs.setai && !inputs.prepared_docs && !inputs.message){
    document.getElementById('out').innerHTML = '<p class="spin">画像を選ぶか、フォームを入力してね</p>'; return;
  }
  const go = document.getElementById('go-check');
  go.disabled = true;
  await post(inputs, files.length ? '画像を読み取ってチェック中…（10秒前後）' : 'チェック中…（数秒）');
  go.disabled = false;
}
</script>
</body>
</html>"""


def _form_fields_html():
    """開発UIのチェック用フォームを rules.py の定義から生成（源内側の登録JSONと同じ項目）。"""
    opts = "".join(
        f'<option value="{v}">{t}</option>' for t, v in rules.JUKYO_ITEMS
    )
    setai = "".join(
        f'<label><input type="checkbox" name="setai" value="{v}"> {t}</label>'
        for t, v in rules.SETAI_ITEMS
    )
    docs = "".join(
        f'<label><input type="checkbox" name="prepared_docs" value="{d}"> {d}</label>'
        for d in rules.PREPARED_DOC_ITEMS
    )
    return (
        '    <fieldset><legend>住まいと通勤</legend>'
        f'<select id="jukyo"><option value="">（選択しない）</option>{opts}</select></fieldset>\n'
        f'    <fieldset><legend>世帯の状況</legend>{setai}</fieldset>\n'
        f'    <fieldset><legend>用意した書類</legend>{docs}</fieldset>'
    )


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    """開発確認用UI。APIキーを埋め込むためトンネル越し（cf-ray付き）には返さない。"""
    if request.headers.get("cf-connecting-ip") or request.headers.get("cf-ray"):
        return HTMLResponse("Not Found", status_code=404)
    html = UI_HTML.replace("__FORM_FIELDS__", _form_fields_html())
    return HTMLResponse(html.replace("__API_KEY__", EXAPP_API_KEY))


@app.post("/")
async def handle(request: Request):
    if not _authorized(request):
        return JSONResponse({"outputs": "認証エラー"}, status_code=401)

    payload = await request.json()
    inputs = payload.get("inputs", {}) if isinstance(payload, dict) else {}

    images = _images_from_files(inputs.get("files"))
    form = {
        "jukyo": (inputs.get("jukyo") or "").strip(),
        "setai": _multi(inputs.get("setai")),
        "prepared_docs": _multi(inputs.get("prepared_docs")),
    }
    message = (inputs.get("message") or inputs.get("question") or "").strip()
    # application_text は旧登録（テキストのみのチェック）との互換キー
    legacy_text = (inputs.get("application_text") or inputs.get("text")
                   or inputs.get("input_text") or "").strip()

    has_form = bool(form["jukyo"] or form["setai"] or form["prepared_docs"])

    # ① チェックモード（画像・チェック用フォーム・旧テキスト入力のいずれかがある）
    if images or has_form or legacy_text:
        logger.info("check: images=%d form=%s text=%d文字",
                    len(images), has_form, len(message or legacy_text))
        try:
            return {"outputs": check.check(message or legacy_text, images, form)}
        except Exception as e:
            logger.exception("チェックに失敗")
            return {"outputs": f"チェック中にエラーが発生しました: {type(e).__name__}: {e}"}

    # ② 相談モード
    if message:
        # 利用者の入力そのものはログに残さない（共有アカウントかつ公開環境のため）
        logger.info("chat: %d文字", len(message))
        try:
            return {"outputs": chat.chat(message, inputs.get("conversation_history") or "")}
        except Exception as e:
            logger.exception("相談への応答に失敗")
            return {"outputs": f"エラーが発生しました: {type(e).__name__}: {e}"}

    return {"outputs": "相談したいことを入力するか、申込書の画像・フォームを入力してください。"}


# --------------------------------------------------------------------------
# AWS Lambda（コンテナイメージ）のエントリポイント
#   ローカル: uvicorn main:app / Lambda: main.handler
# --------------------------------------------------------------------------
try:
    from mangum import Mangum

    handler = Mangum(app, lifespan="off")
except ImportError:  # mangum未導入のローカル環境でも起動できるようにする
    handler = None
