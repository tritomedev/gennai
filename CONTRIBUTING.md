# CONTRIBUTING.md - ドキュメント運用ルール

本リポジトリへのドキュメント追記・更新のルールをまとめています。

---

## 📁 どこに書くか

| 書きたい内容 | 置き場所 |
|---|---|
| 源内の概要・仕様・アーキテクチャ調査 | `docs/01_overview/` |
| コードや技術仕様の調査ログ | `docs/02_research/` |
| 環境構築・セットアップ手順 | `docs/03_setup/` |
| ビルド・デプロイの実施記録 | `docs/04_build/` |
| カスタマイズ案・サービス展開検討 | `docs/05_customization/` |
| Tips・トラブルシュート・気づき | `docs/06_knowledge/` |

迷ったら `docs/06_knowledge/` に書いてOK。後で整理します。

---

## ✍️ ドキュメントの書き方ルール

### 基本

- **Markdown** で記述する
- ファイル名は **英数字・ハイフン区切り**（例: `genai-web-build.md`）
- 各ファイルの先頭に以下のヘッダーを書く

```markdown
# タイトル

- **調査日:** YYYY-MM-DD
- **調査者:** （任意）
- **ステータス:** 調査中 / 完了 / 要確認
```

### 調査ログ

- **わかったこと・わからないこと**を両方書く
- 未解決の疑問点は `TODO:` タグをつける
  ```markdown
  > **TODO:** AWS Bedrockの具体的な設定方法を確認する
  ```
- 参照元URL・コミットハッシュは必ず記載する

### 手順書・ビルドログ

- コマンドは必ずコードブロックに書く
  ```bash
  npm install
  npm run build
  ```
- 実行環境（OS・バージョン等）を冒頭に明記する
- 詰まったポイントは `⚠️ ハマりポイント` セクションとして書き残す

### アイデア・検討事項

- 完成度が低くてもOK、雑でもいいから書く
- 実現可能性・懸念点もセットで書く

---

## 🔀 フォーク運用方針

本リポジトリでは、源内の公式OSSを以下の方針でフォークして利用します。

### フォーク対象

| フォーク元 | 用途 |
|---|---|
| [digital-go-jp/genai-web](https://github.com/digital-go-jp/genai-web) | フロントエンドの動作確認・カスタマイズ検証 |
| [digital-go-jp/genai-ai-api](https://github.com/digital-go-jp/genai-ai-api) | AIアプリの独自実装・拡張検証 |

### ブランチ戦略

```
main          # 安定版・動作確認済みのもの
dev           # 作業ブランチ
feature/xxx   # 個別機能の検証
```

### upstream の追従

公式リポジトリの更新を定期的に確認し、必要に応じてマージする。

```bash
# upstreamを登録（初回のみ）
git remote add upstream https://github.com/digital-go-jp/genai-web.git

# 最新を取得してマージ
git fetch upstream
git merge upstream/main
```

---

## 🏷️ Issue の使い方

GitHub Issueをタスク・調査ログとして活用します。

- 調査タスク → `research` ラベル
- ビルド作業 → `build` ラベル
- バグ・詰まり → `bug` ラベル
- アイデア → `idea` ラベル

Issueテンプレートは `.github/ISSUE_TEMPLATE/` を使ってください。
