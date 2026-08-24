# 一般公開デモ用の共有パスワードログイン（源内Webフォークの改変）

> 環境固有の値は `<...>` のプレースホルダにしている。実値は内部管理の `private/environment.md` を参照。


- **作成日:** 2026-08-24
- **ステータス:** 実装・デプロイ済み（新アカウント <AWS_ACCOUNT_ID> で稼働中）
- **対象:** フォーク `tsucha-nsdq/genai-web` ブランチ `feature/poc-minimal-cost-vpc-disabled`

---

## 目的

源内Webをサンプルとして一般公開するとき、利用者にメールアドレス登録をさせずに触ってもらいたい。
源内のCognitoは `selfSignUpEnabled: false`（管理者発行のみ）かつ `UsernameAttributes: ["email"]`
のため、そのままでは利用者ごとのアカウント発行が必要になる。

そこで**共有アカウントを1つ用意し、サインイン画面をパスワード入力のみに差し替える**。
参考にした公開事例: 源内AI 近藤にこる版（https://digital-supporter.net/genai-nikoru/app/main.htm）

## 2つのモード

| モード | 入口 | 認証 | 権限 |
|---|---|---|---|
| **サンプル参照** | `/` | 共有パスワードのみ（ユーザー名は埋め込み・パスワードは画面に掲載可） | `UserGroup` |
| **管理者** | `/admin-login` | 通常のメール＋パスワード | `UserGroup` + `SystemAdminGroup` |

共有モードを有効にすると Amplify の `<Authenticator>` ごと差し替わるため、
**管理者の入口を別パスとして確保しないとチーム管理・Ex-App登録ができなくなる**。
`/admin-login` はその抜け道で、サインイン後は `location.replace('/')` でルートへ戻す
（このパスには react-router のルート定義がないため）。

## 実装

### CDK（パラメータをビルド時にフロントへ注入）

| ファイル | 変更 |
|---|---|
| `packages/cdk/lib/stack-input.ts` | `sharedLoginUsername: z.string().default('')` を追加 |
| `packages/cdk/lib/construct/web.ts` | `WebProps` に `sharedLoginUsername` を追加し、`VITE_APP_SHARED_LOGIN_USERNAME` として注入 |
| `packages/cdk/lib/generative-ai-use-cases-stack.ts` | `new Web(...)` に `sharedLoginUsername: params.sharedLoginUsername` を追加 |
| `packages/cdk/env-parameters/self-hosting-dev.ts` | `sharedLoginUsername: 'sample-user@example.com'` / `sharedLoginPasswordHint: '<掲載するパスワード>'` |

`sharedLoginPasswordHint` に値を入れると、サインイン画面に
「パスワード ○○○ を入力してください」と**共有パスワードを掲載する**（参考事例と同じ形）。
空文字なら掲載せず「パスワードを入力してください」とだけ表示する。
掲載する＝URLを知っていれば誰でもサインインできる状態になるため、Budgetsアラートが前提。

空文字にすれば通常のサインイン画面に戻る（機能フラグとして働く）。

### フロント

| ファイル | 変更 |
|---|---|
| `packages/web/src/components/auth/SharedPasswordLogin.tsx` | 新規。パスワード入力＋同意チェック＋「源内を利用する」 |
| `packages/web/src/components/auth/AuthWithUserpool.tsx` | `sharedLoginUsername` があり、かつ `/admin-login` でないときに上記へ差し替え |

サインインは `signIn({ username: sharedLoginUsername, password })` を直接呼ぶ。
成功後は `window.location.reload()` して `Authenticator.Provider` にセッションを認識させる。

## Cognitoユーザーの作り方（メールを1通も送らない）

```bash
POOL=<USER_POOL_ID>
USER=sample-user@example.com
PW='<8文字以上・大文字・小文字・数字・記号を含む>'

aws cognito-idp admin-create-user --user-pool-id $POOL --username $USER \
  --user-attributes Name=email,Value=$USER Name=email_verified,Value=true \
  --message-action SUPPRESS --temporary-password "$PW" --profile gennai-prod

aws cognito-idp admin-set-user-password --user-pool-id $POOL --username $USER \
  --password "$PW" --permanent --profile gennai-prod

aws cognito-idp admin-add-user-to-group --user-pool-id $POOL --username $USER \
  --group-name UserGroup --profile gennai-prod
```

- **`--message-action SUPPRESS`** … 招待メールを送信しない
- **`--permanent`** … `FORCE_CHANGE_PASSWORD` を回避し、配布したパスワードでそのまま使える
- **`@example.com`** … RFC 2606 の予約ドメイン。実在しないため他人のアドレスに誤送信しない
- ユーザー名はメール形式である必要がある（`UsernameAttributes: ["email"]`）が、**実在する必要はない**

### パスワードポリシーの制約

デプロイ時の既定は **8文字以上＋大文字＋小文字＋数字＋記号**。
参考事例のような短い共有パスワード（例: `kaiin`）は設定できない。
短くしたい場合は CDK の `passwordPolicy` パラメータを緩めて再デプロイする必要がある。

## 詰まったこと：Authenticator を差し替えると画面が真っ白になる

最初の実装では、共有モードのときに `<Authenticator>` を返さず独自UIだけを返していた。
結果、**一般利用者も管理者も、サインイン後に何も表示されない**状態になった。

- Amplify UI の `useAuthenticator().route` は、`Authenticator.Provider` があるだけでは動かない。
  **`<Authenticator>` コンポーネントがマウントされて初めて `idle` から遷移する**。
- そのため Authenticator を差し替えると `route` が `'idle'` のまま止まり、
  `if (route === 'idle') return null;` のような分岐から永久に抜けられない。
- 管理者も `/admin-login` でのサインイン後にルートへ戻った時点で同じ経路に入るため、同じ症状になる。

**対処: `<Authenticator>` は常にマウントしたままにし、共有モードのときだけ
標準のサインインUIをCSSで隠して独自UIを重ねる。**

```tsx
const sharedMode = Boolean(sharedLoginUsername) && !isAdminLoginPath;

return (
  // 認証後はクラスを外す（children がCSSで隠れる事故を防ぐ）
  <div className={sharedMode && route !== 'authenticated' ? 'shared-login-mode' : undefined}>
    {sharedMode && route === 'signIn' && <SharedPasswordLogin onSubmit={...} />}
    <Authenticator ...>{children}</Authenticator>
  </div>
);
```

```css
.shared-login-mode [data-amplify-authenticator] { display: none; }
```

独自UIを出す条件を `route === 'signIn'` に限定しているのは、
セッション復元中（`idle` / `setup`）にログイン画面がちらつくのを避けるため。

## 一般公開に向けたその他の調整（2026-08-24）

### 会話ごとのコスト表示を隠す

源内は会話ごとに「トークン数：入力 N / 出力 N」「この会話にかかったコスト：N円」を表示する
（`MessageUsageCost` / `DiagramUsageCost`）。これは Bedrock の実トークン数から算出した**実数**のため、
一般公開では利用者が萎縮する・共有アカウントでは他人の利用分まで見える・運用側の原価が露出する。

CDKパラメータ `showUsageCost`（既定 true）を追加し、公開環境では false にした。

| ファイル | 変更 |
|---|---|
| `packages/cdk/lib/stack-input.ts` | `showUsageCost: z.boolean().default(true)` |
| `packages/cdk/lib/construct/web.ts` | `VITE_APP_SHOW_USAGE_COST` として注入 |
| `packages/web/src/features/chat/components/MessageUsageCost.tsx` | 先頭で `return null` |
| `packages/web/src/features/generate-diagram/invoke/components/DiagramUsageCost.tsx` | 同上 |

**呼び出し側ではなくコンポーネント本体で止める**のが要点。呼び出し箇所を個別に潰すより確実で、
upstream が新しい画面で同じコンポーネントを使い始めても自動的に効く。
実際、Vite の定数畳み込みにより**配信JSから該当コードごと消える**（「この会話にかかったコスト」の
文字列が成果物に残らないことを確認済み）。

### トップページの実績数字を差し替え

ランディングに `819 自治体と104社で支える、会員向けAI` と表示していたが、これは参考にした
他サイトの数字であり自環境の実態ではない。一般公開では「819自治体が使っているサービス」と
誤読されるため、数字ブロックごと削除し、事実のみの説明文に置き換えた。

> デジタル庁が公開するオープンソース「源内」をベースにした、行政向け生成AIプラットフォームのサンプル環境です。

なお、チャット画面サイドバーの `MONTHLY USAGE 78%` は**ハードコードされた装飾**であり、
実際の利用量とは無関係（`ChatPage.tsx` にコメントあり）。実数ではないためそのままとした。

## 運用上の注意

1. **会話履歴・利用履歴は全利用者で共有される**。源内の履歴はCognitoユーザー単位のため、
   共有アカウントでは他人の入力が見える。Ex-Appに渡される `x-user-id` も全員同一になり、
   アプリ側でも利用者を区別できない。ログイン画面にその旨の注意書きを表示している。
2. **パスワードを知っていれば誰でも使えるため、Bedrockの従量課金に上限がない**。
   源内Web側にレート制限の仕組みはないので、**Budgetsアラートは必須**。
3. **共有ユーザーに `SystemAdminGroup` を付けないこと**。付けるとEx-App登録やチーム管理まで
   一般利用者ができてしまう。
4. ユーザー名はビルド成果物に含まれるが、パスワードは含めない。ユーザー名の露出だけでは
   サインインできない。

## 動作確認（2026-08-24・ブラウザ実機）

- `/` … パスワード入力のみのサインイン画面が表示され、共有パスワードでサインインできることを確認。
- `/admin-login` … 通常のメール＋パスワード画面が表示され、管理者でサインイン後にトップへ遷移。
  「アカウント」メニューに**チーム管理**が出ることを確認（Ex-App登録が可能な状態）。

## 検証結果（2026-08-24）

配信中のJS（`/assets/index-*.js`）に `sample-user@example.com` / `/admin-login` /
「源内を利用する」がいずれも含まれることを確認。`/admin-login` への直接アクセスは
SPAフォールバックで **200**。
