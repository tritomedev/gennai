"""
港区 子育て支援RAG Ex-App（源内プロトコル準拠）— TASK-034

源内プロトコル:
  POST /  で {"inputs": {...}} を受け、{"outputs": "テキスト(Markdown可)"} を返す。
  ※ ExAppはチャット形式・ストリーミング非対応。1ショットのリクエスト/レスポンスのみ。
    対話的な機能は conversation_history フィールドで疑似的に実現する。

ユースケース:
  区民が「子どもの補助金についてなにか無いかな？」と入力すると、
  ① 今使える制度（区公式サイト由来）と ② これからの動き（区議会で述べられた方針）
  を2段構えで返す。

源内Webへの登録設定（JSON）:
  {
    "input_text": {
      "title": "知りたいこと",
      "desc": "例）子どもの補助金についてなにか無いかな？",
      "type": "textarea",
      "required": true
    },
    "conversation_history": { "title": "会話履歴", "type": "textarea" }
  }

起動:
  .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
"""
import hmac
import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

import rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ward-rag")

app = FastAPI(title="港区 子育て支援RAG (ward-minutes-rag)")

# 源内Webはアプリ登録時のキーを x-api-key ヘッダーで送ってくる（実機観察で確認済み）。
# 公開ホスト前提のため、キーが設定されていれば必ず検証する。
# （未設定ならローカル開発とみなして検証しない）
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


def _authorized(request: Request) -> bool:
    if not EXAPP_API_KEY:
        return True  # ローカル開発モード
    sent = request.headers.get("x-api-key", "")
    return hmac.compare_digest(sent, EXAPP_API_KEY)


@app.get("/")
def health():
    """疎通確認用。"""
    return {
        "status": "ok",
        "app": "ward-minutes-rag",
        "chunks": len(rag.load_index()[1]),
        "llm": rag.LLM_MODEL,
        "embed": rag.EMBED_MODEL,
    }


UI_HTML = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>港区 子育て支援AI（開発確認用）</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, -apple-system, "Hiragino Sans", sans-serif;
         max-width: 780px; margin: 0 auto; padding: 24px 16px 64px; line-height: 1.75; }
  h1 { font-size: 1.25rem; margin-bottom: 4px; }
  .note { color: #888; font-size: .8rem; margin-bottom: 20px; }
  textarea { width: 100%; box-sizing: border-box; padding: 12px; font-size: 1rem;
             border: 1px solid #bbb; border-radius: 8px; font-family: inherit; }
  button { margin-top: 10px; padding: 10px 22px; font-size: 1rem; border: 0;
           border-radius: 8px; background: #1a6dcc; color: #fff; cursor: pointer; }
  button:disabled { background: #999; cursor: default; }
  .samples { margin: 12px 0; display: flex; flex-wrap: wrap; gap: 8px; }
  .samples button { background: #eee; color: #333; font-size: .8rem; padding: 6px 12px; margin: 0; }
  @media (prefers-color-scheme: dark) { .samples button { background:#333; color:#ddd; } }
  #out { margin-top: 28px; border-top: 1px solid #ccc; padding-top: 20px; }
  #out h2 { font-size: 1.05rem; border-left: 4px solid #1a6dcc; padding-left: 10px; margin-top: 28px; }
  #out h3 { font-size: .95rem; }
  #out blockquote { border-left: 3px solid #ccc; margin-left: 0; padding-left: 12px; color: #888; font-size: .85rem; }
  #out table { border-collapse: collapse; }
  .spin { color: #888; }
</style>
</head>
<body>
  <h1>港区 子育て支援AI</h1>
  <div class="note">源内 Ex-App の開発確認用UI（本番の入口は源内Web側）</div>

  <textarea id="q" rows="3" placeholder="例）子どもの補助金についてなにか無いかな？"></textarea>
  <div class="samples">
    <button onclick="setQ(this)">子どもの補助金についてなにか無いかな？</button>
    <button onclick="setQ(this)">ひとり親なんだけど使える手当ある？</button>
    <button onclick="setQ(this)">医療費の助成って何歳まで？</button>
    <button onclick="setQ(this)">学童クラブについて知りたい</button>
  </div>
  <button id="go" onclick="ask()">聞いてみる</button>

  <div id="out"></div>

<script>
function setQ(b){ document.getElementById('q').value = b.textContent.trim(); }
async function ask(){
  const q = document.getElementById('q').value.trim();
  const out = document.getElementById('out');
  const go = document.getElementById('go');
  if(!q){ out.innerHTML = '<p class="spin">質問を入力してね</p>'; return; }
  go.disabled = true;
  out.innerHTML = '<p class="spin">検索して回答を作ってます…（数秒）</p>';
  const t0 = performance.now();
  try{
    const r = await fetch('/', {
      method:'POST',
      headers:{'Content-Type':'application/json', 'x-api-key':'__API_KEY__'},
      body: JSON.stringify({inputs:{input_text:q, conversation_history:''}})
    });
    const d = await r.json();
    const sec = ((performance.now()-t0)/1000).toFixed(1);
    out.innerHTML = marked.parse(d.outputs || '(空の応答)')
      + '<p class="spin">応答 ' + sec + '秒</p>';
    out.querySelectorAll('a').forEach(a=>{a.target='_blank'; a.rel='noopener';});
  }catch(e){
    out.innerHTML = '<p class="spin">エラー: ' + e + '</p>';
  }finally{ go.disabled = false; }
}
document.getElementById('q').addEventListener('keydown', e=>{
  if((e.metaKey||e.ctrlKey) && e.key==='Enter') ask();
});
</script>
</body>
</html>"""


@app.get("/ui", response_class=HTMLResponse)
def ui(request: Request):
    """開発確認用の簡易UI。源内プロトコル（POST /）には影響しない。

    セキュリティ: この画面はAPIキーを埋め込むため、トンネル越し（＝外部公開）の
    アクセスには返さない。cloudflared 経由だと cf-connecting-ip / cf-ray が付くので
    それを判別に使う（実機観察で確認済みの挙動）。
    """
    if request.headers.get("cf-connecting-ip") or request.headers.get("cf-ray"):
        logger.warning("トンネル経由の /ui アクセスを拒否")
        return HTMLResponse("Not Found", status_code=404)
    return HTMLResponse(UI_HTML.replace("__API_KEY__", EXAPP_API_KEY))


@app.post("/")
async def handle(request: Request):
    if not _authorized(request):
        logger.warning("APIキー不一致のリクエストを拒否 (ip=%s)",
                       request.headers.get("cf-connecting-ip", "?"))
        return JSONResponse({"outputs": "認証エラー"}, status_code=401)

    payload = await request.json()
    inputs = payload.get("inputs", {}) if isinstance(payload, dict) else {}
    # 源内は body 直下に sessionId、ヘッダーに x-user-id を付けてくる（実機観察で確認済み）
    session_id = payload.get("sessionId") if isinstance(payload, dict) else None
    user_id = request.headers.get("x-user-id")

    # 源内Webのフォーム定義に合わせる。表記ゆれに一応備える。
    question = (inputs.get("input_text")
                or inputs.get("text")
                or inputs.get("question")
                or "").strip()
    history = (inputs.get("conversation_history") or "").strip()

    if not question:
        return {"outputs": "質問が空でした。知りたいことを入力してください。"}

    # 質問文そのものはログに残さない（共有アカウントかつ公開環境のため）
    logger.info("Q: %d文字 | session=%s user=%s", len(question),
                (session_id or "-")[:8], (user_id or "-")[:8])
    try:
        outputs = rag.answer(question, conversation_history=history)
    except Exception as e:
        logger.exception("生成に失敗")
        return {"outputs": f"エラーが発生しました: {type(e).__name__}: {e}"}

    return {"outputs": outputs}


# --------------------------------------------------------------------------
# AWS Lambda（コンテナイメージ）のエントリポイント
#   ローカル: uvicorn main:app / Lambda: main.handler
# --------------------------------------------------------------------------
try:
    from mangum import Mangum

    handler = Mangum(app, lifespan="off")
except ImportError:  # mangum未導入のローカル環境でも起動できるようにする
    handler = None
