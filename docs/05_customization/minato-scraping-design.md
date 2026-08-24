# 港区 スクレイピング設計（区議会議事録RAG）

- **作成日:** 2026-07-10
- **調査日:** 2026-07-10（TASK-032）
- **ステータス:** 設計確定（TASK-033 実装の入力）
- **前提:** [区議会議事録RAGユースケース](./usecase-ward-minutes-rag.md) で港区を採用済み
- **対象:** 港区の (A) 区民向け子育て・補助金サイト（AsIs）／ (B) 区議会議事録（議論中動向）

---

## 全体方針

- データソースは2系統に分かれ、**技術的性質がまったく異なる**。
  - (A) 子育てサイト = 静的HTML・UTF-8・素直なCMS → スクレイピング容易
  - (B) 議事録 = **セッション状態を持つ旧式ASP・Shift_JIS・検索POST駆動** → 難所
- 二次利用規約は無断転載禁止のため、当面は**社内検証・ローカル閉環境のPOC限定**で扱う（[ユースケース文書](./usecase-ward-minutes-rag.md) 参照）。
- クロールは robots.txt を遵守し、低頻度（1〜2秒間隔）・独自UAで行う。

---

## A. 子育て・補助金サイトのスクレイピング設計

### 起点と構造

- **中核一覧ページ:** `https://www.city.minato.tokyo.jp/kodomo/kate/teate/`（手当て・助成）
- 一覧から各制度の**個別HTMLページ**へリンク。個別ページのURLは制度ごとにトップ階層スラッグがバラバラ（例）:
  - 児童手当: `/kodomokyufu/kodomo/kodomo/jidoteate.html`
  - 児童扶養手当: `/kodomokyufu/kodomo/kate/teate/jidofuyo.html`
  - 児童育成手当: `/kodomokyufu/kodomo/kate/teate/jidoikuse.html`
  - 物価高対応子育て応援手当: `/kodomokyufu/kodomo/kodomo/bukkadakataioukosodateouenteate.html`
  - 子どもタクシー: `/kodomoshien/kodomotakusi.html`
- → **URL推測ではなく、一覧ページ起点でリンクを辿る**設計にする。子育て関連の入口ページ（`/kodomo/kate/teate/`, `/kodomo/kodomo/index.html` 等）を数枚シードにしてBFSで収集。

### 個別ページのDOM抽出

CMS（`tmp_` 接頭辞のガバメント系CMS、文字コードUTF-8）。抽出対象は以下：

| 抽出項目 | セレクタ/目印 |
|---|---|
| 本文コンテナ | `div.col_main` 内の `div#tmp_contents` > `div.page_blog` |
| ページタイトル | `h1`（`#tmp_contents` 直下） |
| 更新日 | `#tmp_update` |
| パンくず（カテゴリ推定） | `#tmp_pankuzu` |
| 除外すべきブロック | `#tmp_reccommend_related` / `#tmp_reccommend_check`（おすすめ・関連の自動生成）、`#cogmo-search-form1/2`（検索ウィジェット）、`#otowidget`（読み上げ） |

- チャンク化はページ＝1制度単位を基本に、長いページのみ見出し（`h2`/`h3`）で分割。
- メタデータに `制度名 / URL / 更新日 / パンくず（カテゴリ）/ 取得日` を保持。

### 難易度: ★2（易）

---

## B. 議事録のスクレイピング設計

### システム特性（実測）

- システム: 会議録研究所「Discuss」系、ドメイン `gikai2.city.minato.tokyo.jp`。
- **文字コード: Shift_JIS（CP932）**。取得後に UTF-8 変換が必須（`iconv -f CP932 -t UTF-8`）。
- **セッション状態を持つ**: 検索フォーム取得時に `Set-Cookie: ASPSESSIONID...` が返る。年選択（`g08v_viewh.asp?Sflg=11&FYY=2025&TYY=2025`）は「令和7年が選択されました」という**サーバ側状態の更新**を返すだけで、静的URLから会議本文へ直行できない。
- 検索フォーム: `POST g07v_search.asp`、主なinput = `FBKEY1`（キーワード）, `ACT`, `KGTP`, `KTYP`, `SORT`, `Sflg`, `s_type`, `NAMES1/2`（発言者）。

### robots.txt 遵守事項（実取得・確定）

- `User-agent: *` の Disallow は `/voices/cgi/`・動画View系ASP・`gikaidoc/index.html` のみ。→ **会議録の本文/検索ページ（`g07v_search.asp` `g08v_viewh.asp` 等）はクロール許可**。
- ただし以下UAは名指しで `Disallow: /`（全面禁止）: CCBot/2.0, **Go-http-client/1.1**, AhrefsBot, SemrushBot, MJ12bot, BaiduSpider, YandexBot ほか多数。
  - → **実装言語の注意**: Go標準 `net/http` のデフォルトUA（`Go-http-client/1.1`）はブロック対象。**必ず独自UAを設定**する。Python `requests`/`httpx` のデフォルトUAは対象外だが、礼儀として明示的UA（連絡先URL付き）を推奨。

### スクレイピング・フロー設計

1. セッション確立: `GET g07v_search.asp` で `ASPSESSIONID` cookie を取得し、以降のリクエストで維持。
2. キーワード検索: `POST g07v_search.asp` に `FBKEY1=子育て`（or 補助金・子ども医療費 等の複数語）＋会議種別・並び順パラメータを付与。
3. 結果一覧をパース → 各会議・発言の本文ページへ遷移して全文HTMLを取得 → UTF-8変換。
4. **POC範囲の限定**: 年（`FYY`/`TYY`）を令和7年（2025）に絞り、直近2〜3定例会分のみ収集。全期間（昭和22年〜）は取り込まない。
5. チャンク化: 発言単位 or 議題単位で分割。メタデータに `定例会名（◯年第◯回）/ 開催日 / 発言者 / 会議種別（本会議・委員会）/ URL / 取得日` を保持。

### 最大の実装リスク

- **セッション遷移の再現**が本タスク最大の難所。ASPの状態遷移（cookie ＋ POST の順序依存）を正しく再現しないと結果ページに到達できない。TASK-033 で最初に潰すべきはここ。
- 代替案: 会議本文が特定URLパターン（KaigiID等）で静的に取れる裏口がないか、TASK-033冒頭で追加探索する。見つかればセッション再現を回避できる。

### 鮮度の扱い

- 港区の公開ラグは会期後およそ2〜3ヶ月。UI表示は「現在議論中」ではなく「**◯年第◯回定例会（開催日）で議論**」と日付メタデータ付きで正直に出す。

### 難易度: ★3（中）— 律速はセッション遷移の再現と Shift_JIS 処理

---

## 実装スタック（想定）

- 収集: Python（`httpx`＋`selectolax`/`lxml`、Shift_JIS対応）。JS実行は不要（サーバHTMLで本文取得可）。
- 整形: 制度＝ページ単位／議事録＝発言・議題単位でチャンク化、メタデータ付与。
- 格納: ベクトルDB（Qdrant想定、[蔵書RAG構成](./usecase-library-rag.md) と共通）。

---

## 次アクション（TASK-033）

1. 議事録の**セッション遷移をPythonで再現**し、キーワード検索→本文取得までを1本通す（または静的URLの裏口を探す）。
2. 子育てサイトを一覧起点でBFS収集し、本文抽出（除外ブロック処理込み）。
3. 直近2〜3定例会＋子育て制度ページをチャンク化してサンプルデータセット化。

> **TODO:** 会議本文の静的URL（KaigiID等）の有無を実装着手時に確認する
> **TODO:** クロール間隔・UA文字列（連絡先URL含む）を実装時に確定し明文化する
