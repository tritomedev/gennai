"""Bedrock呼び出しの共通ラッパー（チェック系・相談系で共用）。"""
import os

import boto3

REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
# jp.anthropic.* はクロスリージョン推論プロファイル（源内バックエンドで有効）。
# 使えない環境向けに nova-lite へフォールバック可能。
LLM_MODEL = os.environ.get("LLM_MODEL", "jp.anthropic.claude-haiku-4-5-20251001-v1:0")
FALLBACK_MODEL = "amazon.nova-lite-v1:0"

bedrock = boto3.client("bedrock-runtime", region_name=REGION)


def converse(system, content, model=None, max_tokens=1200, temperature=0.0):
    """content（テキスト or 画像＋指示のブロック配列）を投げてテキストを得る。"""
    resp = bedrock.converse(
        modelId=model or LLM_MODEL,
        system=[{"text": system}],
        messages=[{"role": "user", "content": content}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    return resp["output"]["message"]["content"][0]["text"].strip()


def converse_with_fallback(system, content, **kw):
    """主モデルが使えない環境では nova-lite で再試行する（画像入力は主モデルのみ）。"""
    try:
        return converse(system, content, **kw)
    except Exception:
        return converse(system, content, model=FALLBACK_MODEL, **kw)
