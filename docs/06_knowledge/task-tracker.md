# タスクトラッカー

> 環境固有の値は `<...>` のプレースホルダにしている。実値は内部管理の `private/environment.md` を参照。


- **最終更新日:** 2026-07-08
- **目的:** 調査・検証タスクを一元管理し、GitHub Issueと自動同期する

---

## 運用ルール

1. **新しいタスクが発生したら、まずこのファイルに追記する**（会話・作業中に思いついたものも含む）
2. 各タスクには `TASK-XXX` の一意なIDを振る（連番、削除しても欠番のままでOK）
3. `docs/06_knowledge/task-tracker.md` をpushすると、GitHub Actionsが自動でIssueと同期する
   - 未完了タスク（`[ ]`）→ 対応するIssueがなければ自動作成
   - 完了タスク（`[x]`）→ 対応するOpen Issueがあれば自動クローズ
4. 同期はタイトルではなく **TASK-ID** で行うため、タスク文言を後から編集してもIssueとの対応関係は壊れない
5. 新規タスクのIDは、このファイル内の最大ID＋1を使う（次に使うIDは末尾の「次のID」を参照）

---

## タスクの分類

- 📖 **調査タスク**：ドキュメント・情報収集で完結するもの → `research` ラベル
- 🔧 **実機検証タスク**：実際に環境を動かして確認する必要があるもの → `build` ラベル

---

## 🔧 実機検証タスク（優先度高）

### 環境構築系

- [x] `TASK-001` genai-webをローカル or VPSで動かしてみる（[ローカル開発環境](https://github.com/digital-go-jp/genai-web/blob/main/docs/%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%AB%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83.md)参照）
  - **完了（2026-07 AWS東京にデプロイ。[../04_build/genai-web-deploy-record.md](../04_build/genai-web-deploy-record.md)）**
  - 要件調査完了（2026-07-08）：**AWSデプロイ回避不能**（ローカルフロント起動もデプロイ済みバックエンド前提）。前提=AWSアカウント＋Bedrockモデルアクセス＋Node22/AWS CLI/CDK/jq。詳細: [genai-web-aws-requirements.md](../03_setup/genai-web-aws-requirements.md)
  - 依存: TASK-025（AWS＋Bedrock準備）→ TASK-026（ツール導入）を先に潰す必要あり
- [ ] `TASK-025` AWSアカウント準備 + Bedrockモデルアクセス有効化（ap-northeast-1／最低限 claude-haiku・nova-lite）
  - 前提確認済み（2026-07-08）：会社アカウント利用可。Budgetsアラート/タグ/撤去の手順は [aws-cost-guardrails.md](../03_setup/aws-cost-guardrails.md)
- [ ] `TASK-026` デプロイ用ツール導入（Node v22.22.2 / AWS CLI＋認証情報 / AWS CDK CLI / jq）
  - 現状（2026-07-08）：jq✅ / npm✅ / Node⚠️v18.20.3（要v22へ）/ AWS CLI❌未導入 / CDK❌未導入
- [x] `TASK-027` genai-webをフォーク&cloneし、最小コスト構成パラメータ（self-hosting-dev.ts）を配置してcdk synthでNAT有無を確認
  - 完了（2026-07-08）：フォーク`tsucha-nsdq/genai-web`をclone、Node22.22.2導入、npm ci、パラメータ配置、synth成功。**NAT Gateway×2を検出（月約¥13,500）**。パラメータvalidationは通過。詳細: [genai-web-minimal-param-design.md](../03_setup/genai-web-minimal-param-design.md)
- [ ] `TASK-028` ExApp用VPCのNAT対策を決めてデプロイ
  - 対策確定・実装済み（2026-07-08）：**①案（VPC撤廃）を実装しsynth実証**。NAT/VPC/EIP/エンドポイント全消滅、固定費¥17,000→¥600/月。**POC限定**（本番はVPC戻す）。詳細: [genai-web-aws-cost-breakdown.md](../03_setup/genai-web-aws-cost-breakdown.md)
  - 残り: 手動作業（コンソール）でBedrockモデルアクセス有効化＋AWS認証情報設定 → `cdk bootstrap` → `cdk deploy`
- [x] `TASK-029` デプロイ実行前提の準備（Bedrockアクセス有効化・AWS認証情報設定）とデプロイ本番
  - **デプロイ成功（2026-07-08）**：`<OLD_CLOUDFRONT_URL>` で稼働。管理者ユーザー発行済み。途中2つの制限に対処（新規アカウントのLambdaメモリ512MB上限 → Aspectでキャップ）。詳細: [genai-web-deploy-record.md](../04_build/genai-web-deploy-record.md)
- [ ] `TASK-030` 源内Webにログインし初期設定（チーム作成）＋ echo-observerを公開ホストしてExApp登録・実リクエスト観察（TASK-002の残り）
- [x] `TASK-002` 最小の自作AIアプリ（FastAPI）を作って源内Webに登録してみる
  - **完了（2026-07-08）**：echo-observerを源内Webに登録し実リクエスト捕捉に成功。仕様書外フィールド（`sessionId`・`x-user-id`）を発見。詳細: [exapp-observation-2026-07-08.md](../04_build/exapp-observation-2026-07-08.md) / ローカル検証: [echo-observer-local-verification.md](../04_build/echo-observer-local-verification.md)
- [ ] `TASK-003` OxigenAI（Lawsy Rust再実装）を実際に動かして源内プロトコル互換性を検証する

### LLM接続の検証（完了：2026-07-08）

- [x] `TASK-004` 【最優先】源内Web内蔵チャットのLLM接続を自作アプリと共有できるか確認する
  - 結論：共有不可（実機検証記事で確定）。詳細: [verified-findings-2026-07-08.md](../02_research/verified-findings-2026-07-08.md)
- [ ] `TASK-005` 自作AIアプリの認証（x-api-key）の発行・管理方法を実際に確認する

### RAGアプリ試作系

- [ ] `TASK-006` Ollama + Qwen2.5（またはLlama 3.1）でローカルLLM環境を構築する
- [x] `TASK-007` pgvector or QdrantでベクトルDBを構築し、サンプル文書を格納する
  - **完了（2026-07-13）**：Qdrant（Docker, `gennai-qdrant`, :6333）＋ Bedrock `cohere.embed-multilingual-v3`（1024次元）でコレクション`minato_kosodate`に投入。港区サンプル24レコード→**106チャンク**。実ユースケース質問で2段検索（現行制度/議論中）の動作を確認。知見：①Cohere v3は512トークン上限のためチャンク分割必須 ②`group_by=doc_id`でグループ化しないと長い制度ページが上位を独占する（実測でトップ5が1制度で埋まる事故）。詳細: [../../apps/ward-minutes-rag/README.md](../../apps/ward-minutes-rag/README.md)
- [ ] `TASK-008` 最小の蔵書RAGアプリを試作し、源内Webに登録して動作確認する
- [ ] `TASK-009` 会話履歴（conversation_history）機能を実装して動作確認する

### 区議会議事録RAG（区民向け補助金ユースケース）試作系

対象区の候補：港区／中央区／江戸川区。区民が「子どもの補助金について何かないか」と自然言語で尋ねると、区民向けサイトから現行制度（AsIs）を、議事録から現在議論中の将来的な動向を提示するEx-App。

- [x] `TASK-033` 確定した1区で議事録スクレイピング→整形パイプラインを試作する（直近2〜3定例会分に限定）
  - **方針転換のうえ完了（2026-07-10）**：RAG価値証明にはサンプル実データで十分との判断で「小さな実データのサンプルデータセット整備」に軽量化。港区で24レコード生成（現行制度11＝静的HTML自動取得／議論中13＝区長所信表明を手キュレーション）。議事録ASPのセッション攻略は本格スクレイパ側（TASK-036）に分離。成果物: [../../apps/ward-minutes-rag/](../../apps/ward-minutes-rag/)
- [ ] `TASK-034` 議事録RAG Ex-App（現行制度＋議論中動向の2段出力）を試作し、源内Webに登録して動作確認する
  - **試作＋ローカル動作確認まで完了（2026-07-13）**：`apps/ward-minutes-rag/`（`rag.py`＝検索/生成コア、`main.py`＝源内プロトコルのFastAPI）。`POST /` がHTTP200・約2秒で2段構えMarkdownを返すことを確認。回答中の金額等が原文に実在することを検証し**幻覚なしを確認**。URLはLLMに書かせずpayloadから機械出力するため出典の幻覚は構造的に発生しない。
  - **残り**：源内Webへの登録・実機確認（ローカル起動のままでは源内Webから到達不可＝公開ホストが必要。TASK-030と同じ論点）
  - **判明**：Bedrockの**Claude系はモデルアクセス未有効でアクセス拒否**（`nova-lite`のみ利用可）。コンソールで有効化すれば環境変数`LLM_MODEL`の変更だけで切替可能。
  - **既知の課題**：①スコア閾値がなく該当制度が無い質問でも上位5件を返す（「一時預かりの支援は？」に無関係な児童手当等が混ざる実測あり）→「該当なし」と返せるようにする ②出典セクションがLLMの引用外ソースも列挙する。詳細: [../../apps/ward-minutes-rag/README.md](../../apps/ward-minutes-rag/README.md)
- [ ] `TASK-036` 【後回し】議事録ASP（gikai2, セッション駆動）の本格スクレイパを実装する。Ex-Appの価値証明後に着手。設計: [../05_customization/minato-scraping-design.md](../05_customization/minato-scraping-design.md)

### 保育所申請書チェック（区民向け・処理型ExApp）試作系

区民が記入した認可保育所の申込内容を入力すると、記入漏れ・必要書類の不足・基本要件の該当性をチェックして指摘する処理型Ex-App。認可保育所の入所申請・選考は区市町村の事務のため、チェック基準は区（港区で継続）の「入園のしおり」等から取得する。申請書は個人情報を含むためPOCはダミー申請書で行い、出力は「参考・最終確認は窓口」と明示して誤判定リスクに備える。

- [x] `TASK-037` 港区の認可保育所申込の必要書類・記入要領・選考基準（利用調整指数＝点数表）を調査し、チェックルールの素材にする（申込のしおり等の入手可否・形式も確認）
  - **完了（2026-07-24）**：令和8年度「ごあんない」PDF（全44p）に事由別必要書類・指数表（基準＋調整17項目＋優先13段階）・記入要領・よくある不備まで集約。一次ソースURL確定。ルールベース＋LLMのハイブリッド設計を決定。詳細: [../05_customization/usecase-hoikusho-check.md](../05_customization/usecase-hoikusho-check.md)
- [ ] `TASK-038` 保育所申請書チェックExApp（記入漏れ・必要書類・要件該当の2段チェック出力）を試作し、源内Webに登録して動作確認する。POCはダミー申請書・テキスト入力から、次段でファイルアップロード対応
  - **試作＋ローカル動作確認まで完了（2026-07-24）**：`apps/hoikusho-check/`（`rules.py`＝調査の機械可読化、`check.py`＝LLM抽出＋ルールエンジン＋テンプレ整形、`main.py`＝源内プロトコルFastAPI）。`POST /` がHTTP200・約2秒で2段（①不備・要確認 ②指数目安）を返す。**指数計算はPythonで決定的**（算数ミス防止）、**書類は保護者ごとに判定**（実測で「母の就労証明書だけ未提出」を正検出）。冒頭に免責明示。
  - **発見**：Bedrock `jp.anthropic.claude-haiku-4-5`（源内と同じClaude 4.5 Haiku）が本アプリの認証でも利用可（`jp.anthropic.*`プロファイルは有効／直IDの`anthropic.claude-3-*`は拒否）。→ ward-minutes-ragのLLMもこれに差し替えれば品質向上可能。
  - **OCR型チェック追加（2026-07-24）**：申込書の画像（スマホ写真）を **Claude 4.5 Haikuのビジョン機能**で読み取り→既存ルールエンジンで点検。源内fileコンポーネント（Base64）と確認用UIの画像アップロードに対応。テスト画像で「母の就労証明書不足・希望園コード空欄・署名空欄」を正検出（3.5秒）。外部OCRエンジン不要。※実写真（手書き・傾き）での精度は要検証。
  - **入力設計を刷新（2026-07-30）**：源内Web側の登録JSONがテキストエリア1個だったため、源内の画面に画像アップロード欄が出ていなかった。登録定義を6項目に拡張し、①自由入力（`message`）＋`conversation_history`＝**相談モード**、②画像（`file`／複数可）＋住まいと通勤（`select`）＋世帯の状況（`checkbox`）＋用意した書類（`checkbox`）＝**チェックモード**の2モード構成にした。画像・チェック用フォームのいずれかがあればチェック、それ以外は相談に自動分岐。登録用JSONは `GET /schema` が返す（定義と実装の二重管理を回避）。
  - **フォーム入力はOCR結果を上書き**（人の明示入力を優先）。「父の就労証明書」のように役割付きで指定された書類は、OCR側の役割なし記述（「就労証明書」）を破棄してから判定する（役割不明＝暫定OKで不足を見逃すため）。
  - **既存バグを2件修正**：①必要書類の照合キーワードが先勝ちで、「本人確認書類」「個人番号確認書類」が「確認書」に誤マッチし**不足を検出できていなかった**（最長一致に修正）。②事由が読み取れない入力でも指数を算出して表示していた（算出不可を明示するよう修正）。
  - **残り**：源内Web登録・実機確認（公開ホスト要）→ `TASK-040`。指数表の全量化は次段。詳細: [../../apps/hoikusho-check/README.md](../../apps/hoikusho-check/README.md)
- [ ] `TASK-039` 保育所申込「作成支援」ExApp（状況を入力すると記入案・記入例・必要書類リストを生成）を試作する。チェック系統（TASK-038）とルール（rules.py）を共用し、2系統（作成支援＋OCRチェック）で展開する
  - **一部着手（2026-07-30）**：相談モード（`chat.py`）として同一ExApp内に実装。`rules.KNOWLEDGE_MD`の範囲で質問に回答し、範囲外は窓口案内に倒す。記入案・記入例の生成は未実装。
- [ ] `TASK-040` 新しいリクエスト定義JSON（`GET /schema`）を源内Webに登録し、`file`／`checkbox`／`select`／`conversation_history`の実挙動を確認する（複数ファイルの可否・ファイルサイズ上限・checkboxの返却形式・会話履歴の実フォーマット）。仕様書に記載がなく実機でしか確認できない
  - **AWS移設は完了（2026-08-22）**：hoikusho-check を新アカウント（<AWS_ACCOUNT_ID>）の Lambda + Function URL にデプロイし、health 200／認証なし401／相談モード200（1.4秒）を確認。IaCは `apps/infra/`（CDK）。アクセスキー不要（実行ロールでBedrock）、APIキーはSecrets Manager自動生成。記録: [../04_build/exapp-aws-deploy-record.md](../04_build/exapp-aws-deploy-record.md)
  - **残り**：源内Web本体が旧アカウントにしかないため、新アカウントへのデプロイ後に登録・実機確認する
- [x] `TASK-041` Bedrockの「Anthropic 利用用途フォーム（use case details）」を新アカウント <AWS_ACCOUNT_ID> で提出し、Claudeの呼び出しを復旧する
  - **完了（2026-08-24）**：`jp.anthropic.claude-haiku-4-5` が開通。本番Lambdaで相談モード3.8秒・画像OCRチェック3.5秒を確認。
  - **手順の変更に注意**：Bedrockコンソールの「モデルアクセス」ページは**廃止済み**（Model access page has been retired）。現在はモデル初回呼び出し時に自動で有効化される方式。ただし**Anthropicモデルだけは初回にユースケース詳細の提出が必要**で、そのフォームは**プレイグラウンドでモデルを開いたときに表示される**（モデルカタログ → Claude Haiku 4.5 → プレイグラウンド）。
  - **紛らわしい点**：`aws bedrock get-foundation-model-availability` の `agreementAvailability` は判定に使えない。呼び出しに成功する `claude-sonnet-4-6` でも `NOT_AVAILABLE` と表示される。可否は実際に `converse` を投げて確認するのが確実。
  - フォーム送信の反映には**十数分かかる**（送信直後は同じエラーが返る。エラー文の "try again in 15 minutes" のとおり）。
- [x] `TASK-042` 源内Web本体を新アカウント（<AWS_ACCOUNT_ID>）にデプロイする。旧アカウント <OLD_AWS_ACCOUNT_ID> からの移行
  - **完了（2026-08-22）**：`https://tritome-gennai-sample.com` で稼働（CloudFront 200）。所要8分20秒。追加で必要だったのは us-east-1 の bootstrap のみ。**NAT Gateway 0件・追加VPC 0件**を実測で確認（VPC撤廃の改変は正常に機能）。記録: [../04_build/genai-web-deploy-record.md](../04_build/genai-web-deploy-record.md)
  - **知見**：`cdk.out` は消さずに書き足されるため、`bootstrap` 時（`-c env` 無し＝既定パラメータ）に生成された**VPCありのテンプレートが残骸として残る**。ワイルドカードでgrepすると誤検出する。検査前に `rm -rf cdk.out` するか、対象テンプレートをファイル名で特定すること。
  - **残り**：Cognito管理者作成／チーム作成→ExApp登録／Budgets設定／Lambdaメモリ緩和申請／旧アカウントの撤去判断
- [x] `TASK-044` 一般公開デモ用に、メール登録なしで使える共有パスワードログインを実装する（管理者モードとサンプル参照モードの分離）
  - **完了（2026-08-24）**：サンプル参照は `/` でパスワードのみ、管理者は `/admin-login` で通常のメール＋パスワード。CDKパラメータ `sharedLoginUsername` を空にすれば通常のサインイン画面に戻る。Cognitoユーザーは `--message-action SUPPRESS` ＋ `--permanent` で**メール0通**で発行できる。設計・手順: [../05_customization/shared-login-for-public-demo.md](../05_customization/shared-login-for-public-demo.md)
  - **注意**：共有モードは `<Authenticator>` ごと差し替わるため、管理者用の入口を別パスで確保しないとチーム管理・Ex-App登録ができなくなる。
  - **ハマりどころ（実測）**：`<Authenticator>` を差し替えると `useAuthenticator().route` が `'idle'` のまま進まず、**画面が何も表示されなくなる**（管理者もサインイン後に同症状）。Authenticator は常にマウントし、共有モード時だけ標準UIをCSSで隠して独自UIを重ねる形に修正した。
  - **未対応**：共有アカウントは会話履歴・利用履歴が全利用者で共有される。Bedrock課金の上限もないため Budgets アラートが前提（`TASK-045`）
- [x] `TASK-045` 新アカウント <AWS_ACCOUNT_ID> に Budgets アラートを設定する
  - **完了（2026-08-24）**：`gennai-monthly-20usd`（月$20 ≒ ¥3,000）。通知は実績50%・実績100%・予測100%の3本、宛先 <ADMIN_EMAIL>。設定時点の実績は $0.18。
  - **判明**：Budgets の `BudgetLimit.Unit` に **`JPY` は指定できない**（`JPY is not in the supported unit set: [USD]`）。CLIで作る場合はUSD建てにする。
- [x] `TASK-043` ward-minutes-rag の Qdrant（Docker）依存を外し、埋め込み済みベクトルを同梱したメモリ内検索に置き換えてLambdaに載せる
  - **完了（2026-08-24）**：`scripts/build_index.py` で 24レコード→106チャンクを埋め込み、`data/index/`（vectors.npy 424KB＋chunks.json 136KB）に出力してイメージへ同梱。`rag.retrieve()` は Qdrant の `query_points_groups(group_by="doc_id")` と同じ挙動を numpy で再現（保存時にL2正規化しておき内積＝コサイン類似度）。**下流（`_group_to_source` 以降）は無改修**。
  - **ベクトルDBは不要と判断**：この規模ならOpenSearch Serverless等は月5万円規模の固定費に見合わない。Lambda同梱で十分（本番実測6.9秒）。
  - **LLMを nova-lite → Claude Haiku 4.5 に変更**（TASK-041で開通したため）。回答品質が向上。
  - **やらかし（記録）**：2本目のExAppを作る際、1本目に入れた Secrets Manager からのAPIキー取得（`_load_api_key`）の移植を忘れ、**数分間 Function URL が無認証で公開された**。`EXAPP_API_KEY` が空だと `_authorized` が常にTrueを返す実装のため、認証が素通りする。→ 修正後に**認証なし401 / 認証あり200** を両アプリで確認。**新しいExAppを追加したら必ず認証なしPOSTで401を確認すること**。
- [x] `TASK-040` の実機確認（源内Web経由）
  - **完了（2026-08-24）**：管理者で2アプリを登録し、一般ユーザー（共有アカウント）から画像OCRチェックが動作することを確認。
  - **判明した仕様（公式ドキュメントに記載なし）**：`file` コンポーネントには `multiple` / `max_file_count` / `accept` / `max_size` の4オプションがある。**`multiple` の既定は false で、2枚目を選ぶと1枚目が上書きされる**。`max_size` は `"5MB"` のような文字列で指定する（`ai-app-api-spec.md` の「max_sizeのデフォルト値を確認する」TODOはこれで回収）。`checkbox` / `select` は `{title, value}` の items 形式で受け付けられた。
  - **同時に見つかったアプリ側のバグ**：複数画像を渡しても、申込書の「添付書類」欄の記載しか `prepared_docs` に入らず、**画像として提出された書類そのものを数えていなかった**。プロンプトに「画像1枚1枚が提出された書類」と明記して解消。
  - **表示の不整合も修正**：フォーム未選択時、画像から読み取った住まい（区外在住など）が「①読み取った内容」に出ず、「②−9されます」の根拠が画面上で追えなかった。
- [x] `TASK-046` 一般公開に備えて、利用者の入力がCloudWatch Logsに残らないようにする
  - **完了（2026-08-24）**：両アプリとも入力本文のログ出力をやめ**文字数のみ**に変更（相談モードの入力60文字・RAGの質問80文字を出していた）。画像は元からログに出していない。あわせて**入力欄の説明文**に「全員が同じアカウントを共有します。実在の氏名・住所などの個人情報は入力しないでください」を追記。
- [x] `TASK-047` 独自ドメインを取得して源内Webに設定する
  - **完了（2026-08-24）**：Route 53 で **`tritome-gennai-sample.com`** を取得（$16/年・自動更新ON）。ホストゾーン `<HOSTED_ZONE_ID>` は取得時に自動作成された。**apex と www の両方で HTTPS 200 を実測**（証明書検証エラーなし、有効期限 2027-03-09・ACMが自動更新）。
  - **本家CDKは apex 非対応だったため3箇所を改変**：証明書・CloudFrontの代替ドメイン・Aレコードのいずれも `hostName` 必須で `${hostName}.${domainName}` 固定だった。`hostName: ''` でルートドメイン運用できるようにし、`www` もSANとAレコードでカバー。**apexにCNAMEは張れないが Route 53 の Alias なら張れる**点を利用。
  - **費用**：ドメイン $16/年 ＋ ホストゾーン $0.50/月 ＝ **年約¥3,300**。**SSL証明書は $0**。
- [ ] `TASK-048` ward-minutes-rag の検索にスコア閾値を設ける（該当制度が無い質問でも常に上位5件返すため、無関係な制度が回答に混ざる）
- [ ] `TASK-049` ward-minutes-rag の出典セクションを、回答本文で実際に引用されたタグ（[S1] 等）に絞り込む
- [ ] `TASK-050` Ex-Appのコールドスタート対策を検討する。ward-minutes-rag はコンテナ入れ替え直後に17秒かかった実測があり、**源内の29秒タイムアウト**に対する余裕が小さい（通常時は6〜7秒）

---

## 📖 調査タスク

### 完了

- [x] `TASK-010` 源内の概要・アーキテクチャ調査
- [x] `TASK-011` genai-web / genai-ai-apiの構成調査
- [x] `TASK-012` AIアプリAPI仕様の調査
- [x] `TASK-013` Lawsyの内部構造調査（OxigenAIから逆解析）
- [x] `TASK-014` 国内LLM候補調査
- [x] `TASK-015` 源内の価値と限界の整理
- [x] `TASK-016` 対話型 / 処理型アプリの分類

### 未着手

- [ ] `TASK-017` e-Gov法令APIの仕様調査（データ取得フロー）
- [ ] `TASK-018` BigQueryのembedding生成方法の調査（Vertex AI Embeddings API？）
- [x] `TASK-019` Lawsy公式READMEの直接確認（GitHub bot制限の回避方法を探す）
  - 結論：直接取得は不可のままだが、実機検証記事で3テンプレートの内部構成を代替確認。詳細: [verified-findings-2026-07-08.md](../02_research/verified-findings-2026-07-08.md)
- [x] `TASK-020` tsuzumi 2のオンプレ版の料金・調達方法
  - 結論：個人向け提供なし、法人向け個別商談制。詳細: [verified-findings-2026-07-08.md](../02_research/verified-findings-2026-07-08.md)
- [ ] `TASK-021` 2026年8月の国内LLM試用開始後の評価結果を追う
- [ ] `TASK-022` 蔵書のOCR精度確保の方法論調査
- [ ] `TASK-023` チャンク分割の最適サイズ調査（書籍データの場合）
- [ ] `TASK-024` 著作権・利用規約の確認（アーカイブ蔵書のデジタル利用条件）
- [x] `TASK-031` 港区・中央区・江戸川区の区議会議事録の公開状況を調査する（公開システム・フォーマットHTML/PDF・robots.txt・利用規約/二次利用条件・公開ラグ）。区の選定判断材料とする
  - **完了（2026-07-10）**：3区とも技術的取得は可能だが二次利用は全区「無断転載禁止」。中央区はrobots.txtがAIボット全面ブロック＋会議録`.cgi`禁止で除外候補。港区＝鮮度最良（2〜3ヶ月）、江戸川区＝子育てネタ最豊富だが公開ラグ5ヶ月。詳細: [../05_customization/usecase-ward-minutes-rag.md](../05_customization/usecase-ward-minutes-rag.md)
- [x] `TASK-032` 選定した区の区民向け子育て・補助金制度ページの構造を確認する（スクレイピング設計のため）
  - **完了（2026-07-10／港区）**：子育てサイトは静的HTML・UTF-8で★2（易）。議事録はセッション状態を持つ旧式ASP＋Shift_JISで★3、検索は`POST g07v_search.asp`（キーワード`FBKEY1`）。robots.txtは本文許可だがGo-http-client/CCBotは名指し禁止。設計: [../05_customization/minato-scraping-design.md](../05_customization/minato-scraping-design.md)
- [ ] `TASK-035` 著作権法40条（公開の政治上の演説・陳述の利用）が区議会議事録のRAG利用にどこまで及ぶか調査する（サイト利用規約より上位の法律論／編集利用の制限／区職員の制度説明文は対象外の点）

---

## 検証で分かったら更新すべきドキュメント

| 検証項目 | 更新先ドキュメント |
|---|---|
| LLM接続共有の可否（TASK-004） | `docs/01_overview/gennai-value-and-limits.md` |
| genai-webのローカル/VPS動作可否（TASK-001） | `docs/03_setup/` 配下に新規ファイル作成 |
| 自作AIアプリの動作確認結果（TASK-002） | `docs/04_build/` 配下に新規ファイル作成 |
| RAGアプリ試作の結果（TASK-006〜009） | `docs/05_customization/usecase-library-rag.md` |

---

## 次に使うID

`TASK-051`
