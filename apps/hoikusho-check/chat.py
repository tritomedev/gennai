"""
相談モード（AIと会話して業務を進める）。

源内の疑似チャット（conversation_history）に対応し、港区の申込みルールの範囲で質問に答える。
判定・点数計算は行わない（それはチェックモード＝check.py の役割）。
"""
import llm
import rules

MAX_HISTORY_CHARS = 4000  # 源内から返ってくる会話履歴が伸びても入力を膨らませすぎない


def chat(message, history=""):
    """自由記述の相談 → 回答Markdown。"""
    message = (message or "").strip()
    if not message:
        return "相談したいことを入力してください。"

    history = (history or "").strip()
    if len(history) > MAX_HISTORY_CHARS:
        history = "…（省略）\n" + history[-MAX_HISTORY_CHARS:]

    text = ""
    if history:
        text += f"これまでの会話:\n{history}\n\n"
    text += f"区民からの相談:\n{message}"

    answer = llm.converse_with_fallback(
        rules.CHAT_SYSTEM, [{"text": text}], max_tokens=900, temperature=0.2
    )
    return f"{answer}\n\n> {rules.DISCLAIMER}"
