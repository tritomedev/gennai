# タスクトラッカー

- **最終更新日:** 2026-07-08
- **目的:** 調査・検証タスクを一元管理する

---

## タスクの分類

- 📖 **調査タスク**：ドキュメント・情報収集で完結するもの
- 🔧 **実機検証タスク**：実際に環境を動かして確認する必要があるもの

---

## 🔧 実機検証タスク（優先度高）

### 環境構築系

- [ ] genai-webをローカル or Proxmoxで動かしてみる（[ローカル開発環境](https://github.com/digital-go-jp/genai-web/blob/main/docs/%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83.md)参照）
- [ ] 最小の自作AIアプリ（FastAPI）を作って源内Webに登録してみる
- [ ] OxigenAI（Lawsy Rust再実装）を実際に動かして源内プロトコル互換性を検証する

### LLM接続の検証（最優先・今日の議論より）

- [ ] **源内Web内蔵チャットのLLM接続を自作アプリと共有できるか確認する**
  - 源内Web管理画面・AIアプリ開発ガイドにLLMプロキシAPIの記載がないか確認
  - もしあれば、LLM個別調達が不要になり、コスト構造が大きく変わる
  - 関連: [gennai-value-and-limits.md](../01_overview/gennai-value-and-limits.md) の「未確認：源内Web内蔵チャットのLLM接続は自作アプリと共有できるか」セクション
- [ ] 自作AIアプリの認証（x-api-key）の発行・管理方法を実際に確認する

### RAGアプリ試作系

- [ ] Ollama + Qwen2.5（またはLlama 3.1）でローカルLLM環境を構築する
- [ ] pgvector or QdrantでベクトルDBを構築し、サンプル文書を格納する
- [ ] 最小の蔵書RAGアプリを試作し、源内Webに登録して動作確認する
- [ ] 会話履歴（conversation_history）機能を実装して動作確認する

---

## 📖 調査タスク

### 完了

- [x] 源内の概要・アーキテクチャ調査
- [x] genai-web / genai-ai-apiの構成調査
- [x] AIアプリAPI仕様の調査
- [x] Lawsyの内部構造調査（OxigenAIから逆解析）
- [x] 国内LLM候補調査
- [x] 源内の価値と限界の整理
- [x] 対話型 / 処理型アプリの分類

### 未着手

- [ ] e-Gov法令APIの仕様調査（データ取得フロー）
- [ ] BigQueryのembedding生成方法の調査（Vertex AI Embeddings API？）
- [ ] Lawsy公式READMEの直接確認（GitHub bot制限の回避方法を探す）
- [ ] tsuzumi 2のオンプレ版の料金・調達方法
- [ ] 2026年8月の国内LLM試用開始後の評価結果を追う
- [ ] 蔵書のOCR精度確保の方法論調査
- [ ] チャンク分割の最適サイズ調査（書籍データの場合）
- [ ] 著作権・利用規約の確認（アーカイブ蔵書のデジタル利用条件）

---

## 検証で分かったら更新すべきドキュメント

| 検証項目 | 更新先ドキュメント |
|---|---|
| LLM接続共有の可否 | `docs/01_overview/gennai-value-and-limits.md` |
| genai-webのローカル/Proxmox動作可否 | `docs/03_setup/` 配下に新規ファイル作成 |
| 自作AIアプリの動作確認結果 | `docs/04_build/` 配下に新規ファイル作成 |
| RAGアプリ試作の結果 | `docs/05_customization/usecase-library-rag.md` |
