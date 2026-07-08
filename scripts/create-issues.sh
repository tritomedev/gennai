#!/bin/bash
# create-issues.sh
# タスクトラッカーの内容をGitHub Issueとして一括作成するスクリプト
#
# 使い方:
#   cd ~/SESProjects/GENNAI-project
#   sh scripts/create-issues.sh
#
# 前提: gh auth login 済みであること

set -e

REPO="tritomedev/gennai"

echo "=== ラベルを作成します（既にある場合はスキップ） ==="

gh label create "research" --repo "$REPO" --color "0E8A16" --description "調査タスク" 2>/dev/null || echo "research ラベルは既に存在します"
gh label create "build" --repo "$REPO" --color "1D76DB" --description "ビルド・実装タスク" 2>/dev/null || echo "build ラベルは既に存在します"

echo ""
echo "=== 実機検証タスク（優先度高）を作成します ==="

gh issue create \
  --repo "$REPO" \
  --title "genai-webをローカル or VPSで動かしてみる" \
  --body "ローカル開発環境の手順を確認しながら実際に動かす。

参照: https://github.com/digital-go-jp/genai-web/blob/main/docs/ローカル開発環境.md

## 完了条件
- [ ] ローカルでUIが起動する
- [ ] 結果を docs/03_setup/ に記録する" \
  --label "research"

gh issue create \
  --repo "$REPO" \
  --title "最小の自作AIアプリ（FastAPI）を作って源内Webに登録してみる" \
  --body "AIアプリAPI仕様に準拠した最小構成のアプリを作り、実際に源内Webへ登録できるか確認する。

参照: docs/02_research/ai-app-api-spec.md

## 完了条件
- [ ] FastAPIで /  にPOSTを受けて {\"outputs\": ...} を返すAPIを作成
- [ ] 源内WebのGUIから登録できることを確認
- [ ] 結果を docs/04_build/ に記録する" \
  --label "build"

gh issue create \
  --repo "$REPO" \
  --title "【最優先】源内Web内蔵チャットのLLM接続を自作アプリと共有できるか確認する" \
  --body "源内Web内蔵のチャット機能が使っているLLM接続を、自作AIアプリからも呼び出せるか確認する。
できるならLLM個別調達が不要になり、コスト構造が大きく変わる重要な検証。

参照: docs/01_overview/gennai-value-and-limits.md（未確認：源内Web内蔵チャットのLLM接続は自作アプリと共有できるか）

## 完了条件
- [ ] 源内Web管理画面・AIアプリ開発ガイドにLLMプロキシAPIの記載がないか確認
- [ ] 実際に呼び出しを試して結果を記録
- [ ] 結果を docs/01_overview/gennai-value-and-limits.md に反映" \
  --label "research"

gh issue create \
  --repo "$REPO" \
  --title "OxigenAI（Lawsy Rust再実装）を実際に動かして源内プロトコル互換性を検証する" \
  --body "cargo install oxigenai で導入し、源内Webへの登録可否を確認する。

参照: https://github.com/cool-japan/oxigenai

## 完了条件
- [ ] oxigenai serve でローカル起動
- [ ] 源内プロトコル準拠のレスポンスが返るか確認
- [ ] 結果を docs/02_research/lawsy-deep-dive.md に追記" \
  --label "research"

gh issue create \
  --repo "$REPO" \
  --title "Ollama + Qwen2.5（またはLlama 3.1）でローカルLLM環境を構築する" \
  --body "VPS環境でのローカルLLM運用の実現可能性を検証する。

## 完了条件
- [ ] Ollamaをインストールし、モデルを起動
- [ ] APIとして呼び出せることを確認
- [ ] 結果を docs/03_setup/ に記録する" \
  --label "build"

gh issue create \
  --repo "$REPO" \
  --title "pgvector or QdrantでベクトルDBを構築し、サンプル文書を格納する" \
  --body "図書館蔵書RAGの基盤となるベクトルDBを試作する。

参照: docs/05_customization/usecase-library-rag.md

## 完了条件
- [ ] ベクトルDBを起動
- [ ] サンプル文書を埋め込みベクトル化して格納
- [ ] 検索が機能することを確認" \
  --label "build"

gh issue create \
  --repo "$REPO" \
  --title "最小の蔵書RAGアプリを試作し、源内Webに登録して動作確認する" \
  --body "上記タスクの集大成。実際に質問→蔵書検索→回答が源内Web経由で動くか確認する。

参照: docs/05_customization/usecase-library-rag.md

## 完了条件
- [ ] 蔵書RAGアプリが源内プロトコルに準拠して動作
- [ ] 源内Web経由での動作確認
- [ ] 結果を docs/05_customization/usecase-library-rag.md に追記" \
  --label "build"

echo ""
echo "=== 完了！ Issueを確認するには: ==="
echo "gh issue list --repo $REPO"
