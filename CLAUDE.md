# CLAUDE.md

このファイルはClaude Code（VSCode版含む）がこのリポジトリで作業する際に自動で読み込むコンテキストファイルです。

---

## プロジェクト概要

「源内（GenAI）」はデジタル庁が開発・OSS公開したガバメントAI基盤。
本リポジトリ（gennai）は、源内の調査・ビルド・カスタマイズを行い、源内を活用したサービス展開のアプローチを検討するプロジェクト。

詳細は必ず以下を先に読むこと：

- [README.md](./README.md) — プロジェクト全体像・フォーク元リンク
- [docs/01_overview/what-is-gennai.md](./docs/01_overview/what-is-gennai.md) — 源内の概要
- [docs/01_overview/gennai-value-and-limits.md](./docs/01_overview/gennai-value-and-limits.md) — **最重要**。源内の本質・限界・LLM調達要否の結論

---

## リポジトリ構造

```
gennai/
├── README.md               # プロジェクト概要・ナビゲーション
├── CONTRIBUTING.md          # ドキュメント運用ルール・フォーク方針
├── CLAUDE.md                # このファイル
├── docs/
│   ├── 01_overview/         # 源内とは何か（調査・解析結果）
│   ├── 02_research/         # 技術調査ログ
│   ├── 03_setup/            # 環境構築手順
│   ├── 04_build/            # ビルド・デプロイ記録
│   ├── 05_customization/    # カスタマイズ・サービス展開検討
│   ├── 06_knowledge/        # 知見・タスクトラッカー
│   └── assets/              # 図・画像
├── scripts/                 # 自動化スクリプト（Issue同期等）
└── .github/
    ├── workflows/           # GitHub Actions
    └── ISSUE_TEMPLATE/       # Issueテンプレート
```

---

## 絶対厳守：タスク管理ルール

**新しいタスク・TODO・要検証事項が発生したら、必ず `docs/06_knowledge/task-tracker.md` に追記すること。**

- 作業中に思いついたものも例外なく追記する
- 各タスクには一意な `TASK-XXX` のIDを振る（IDはファイル末尾「次に使うID」を参照し、使用後は数値をインクリメントして更新する）
- 完了したタスクは削除せず `- [x]` にチェックする
- タスクの分類：🔧実機検証タスク（`build`ラベル）／ 📖調査タスク（`research`ラベル）

### 自動Issue同期の仕組み

`docs/06_knowledge/task-tracker.md` をpushすると、GitHub Actions（`.github/workflows/sync-tasks.yml`）が自動発火し、`scripts/sync-tasks-to-issues.py` がMarkdownを解析してGitHub Issueと同期する。

- 未完了タスク（`[ ]`）→ 対応するOpen Issueがなければ自動作成
- 完了タスク（`[x]`）→ 対応するOpen Issueがあれば自動クローズ
- マッチングは**タイトル文字列ではなくTASK-ID**で行う（Issue本文に `Task-ID: TASK-XXX` を埋め込んで対応関係を管理）ため、タスクの文言を後から編集してもIssueとの対応は壊れない

手動同期する場合：
```bash
python3 scripts/sync-tasks-to-issues.py
```

---

## ドキュメント運用ルール（詳細は CONTRIBUTING.md 参照）

- Markdownで記述、ファイル名は英数字ハイフン区切り
- 各ドキュメント冒頭に `作成日` / `調査日` と `ステータス` を明記
- わかったこと・わからないことを両方書く。未解決事項は `> **TODO:**` 形式で明記
- 手順書はコマンドを必ずコードブロックで書き、実行環境を明記する

---

## 確定している重要な技術的結論（前提として必ず踏まえること）

以下は既に調査・実機検証済みで結論が出ている。同じ調査を繰り返さないこと。詳細は各リンク先を参照。

1. **源内はAIではなくオーケストレーター（インターフェース）**。LLM本体は含まない。
   → [gennai-value-and-limits.md](./docs/01_overview/gennai-value-and-limits.md)

2. **源内Web内蔵チャットのLLM接続は自作AIアプリ（ExApp）と共有できない**（実機検証で確定）。自作アプリは常に自前でLLMを調達・接続する必要がある。
   → [verified-findings-2026-07-08.md](./docs/02_research/verified-findings-2026-07-08.md)

3. **自作AIアプリ（ExApp）は源内プロトコルに準拠したREST APIであればよい**。最小実装は `POST /` で `{"inputs": {...}}` を受け `{"outputs": "..."}` を返すだけ。クラウド・言語は自由。
   → [ai-app-api-spec.md](./docs/02_research/ai-app-api-spec.md)

4. **ExAppはチャット形式・ストリーミング非対応**。1ショットのリクエスト/レスポンスのみ。対話的な機能が必要な場合は `conversation_history` フィールドで疑似的に実現する。

5. **源内WebはAWS前提の構成**（genai-webはAWS CDKでデプロイ）。完全ローカル動作は不可（フロントのみローカル起動可能、バックエンドはAWS必須）。さくらのVPS等の自前環境で完結させたい場合は、ExApp（自作AIアプリ）側をローカルLLM（Ollama等）+ ローカルベクトルDB（pgvector/Qdrant）で構築する方針が現実的。
   → [gennai-value-and-limits.md](./docs/01_overview/gennai-value-and-limits.md)

6. **国産LLM（tsuzumi 2等）は法人・公共機関向けの個別商談制で、個人・小規模開発では現実的でない**。小規模検証段階ではOllama＋Qwen2.5/Llama 3.1が現実的な選択肢。
   → [verified-findings-2026-07-08.md](./docs/02_research/verified-findings-2026-07-08.md)

7. **蔵書RAG等のユースケースでは、実装自体より周辺データ整備（OCR精度・チャンク分割・著作権確認）の方が難易度が高い**。
   → [usecase-library-rag.md](./docs/05_customization/usecase-library-rag.md)

---

## 現在の実装フェーズでの優先タスク

`docs/06_knowledge/task-tracker.md` の🔧実機検証タスクを参照。特に以下が未着手の最優先事項：

- `TASK-001` genai-webをローカル or VPSで動かす
- `TASK-002` 最小の自作AIアプリ（FastAPI）を作って源内Webに登録する
- `TASK-006`〜`TASK-009` Ollama + ベクトルDBでの蔵書RAG試作

---

## フォーク運用方針

- `digital-go-jp/genai-web` と `digital-go-jp/genai-ai-api` をフォークして利用する
- 両リポジトリともPull Requestは受け付けていない（公式方針）。フォーク前提で独自改造する
- ブランチ戦略: `main`（安定版） / `dev`（作業） / `feature/xxx`（個別機能）

---

## Claude Codeへの依頼時の心構え

- 実装作業を始める前に、上記「確定している重要な技術的結論」を前提として踏まえること
- 新しい発見・詰まりポイントがあれば `docs/04_build/` または `docs/06_knowledge/` に記録すること
- 環境構築の手順が固まったら `docs/03_setup/` に記録すること
