import { Lock, ShieldCheck, IdCard, ArrowRight, Building2 } from "lucide-react"

export function LoginScreen() {
  return (
    <div className="grid min-h-[720px] lg:grid-cols-2 [font-family:var(--font-body)]">
      {/* 左: ブランドパネル */}
      <div
        className="relative hidden flex-col justify-between overflow-hidden p-10 lg:flex"
        style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
      >
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-[calc(var(--c-radius)*0.6)] bg-[var(--c-primary-fg)] text-lg font-bold"
            style={{ color: "var(--c-primary)" }}>
            源
          </span>
          <span className="text-lg font-bold [font-family:var(--font-heading)]">源内</span>
        </div>

        <div>
          <h1 className="text-3xl font-bold leading-tight [font-family:var(--font-heading)] text-balance">
            行政の現場に、
            <br />
            信頼できる生成AIを。
          </h1>
          <p className="mt-4 max-w-sm text-sm leading-relaxed opacity-90">
            源内は、庁内文書を根拠に回答するセキュアなガバメントAIです。所属アカウントでログインしてください。
          </p>
          <ul className="mt-8 space-y-3 text-sm">
            {[
              { icon: ShieldCheck, t: "LGWAN・閉域環境に対応" },
              { icon: Lock, t: "入力データは外部学習に不使用" },
              { icon: IdCard, t: "職員IDによる権限管理" },
            ].map((f) => (
              <li key={f.t} className="flex items-center gap-3 opacity-95">
                <f.icon className="h-5 w-5 shrink-0" />
                {f.t}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs opacity-70">© 2026 Tri-tome Inc.</p>
      </div>

      {/* 右: フォーム */}
      <div className="flex items-center justify-center bg-[var(--c-bg)] px-6 py-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <span
              className="flex h-9 w-9 items-center justify-center rounded-[calc(var(--c-radius)*0.6)] text-lg font-bold"
              style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
            >
              源
            </span>
            <span className="text-lg font-bold [font-family:var(--font-heading)]">源内</span>
          </div>

          <h2 className="text-2xl font-bold [font-family:var(--font-heading)]">ログイン</h2>
          <p className="mt-2 text-sm text-[var(--c-text-muted)]">
            職員アカウントで源内にサインインします。
          </p>

          {/* 自治体選択 */}
          <div className="mt-8 space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium">所属自治体</label>
              <div
                className="flex items-center gap-2 border px-3 py-2.5"
                style={{ borderColor: "var(--c-border)", borderRadius: "var(--c-radius)", backgroundColor: "var(--c-surface)" }}
              >
                <Building2 className="h-4 w-4 text-[var(--c-text-muted)]" />
                <span className="text-sm">◯◯市役所</span>
              </div>
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium">職員ID</label>
              <input
                type="text"
                placeholder="例: 2026-00123"
                className="w-full border px-3 py-2.5 text-sm outline-none focus:ring-2"
                style={{
                  borderColor: "var(--c-border)",
                  borderRadius: "var(--c-radius)",
                  backgroundColor: "var(--c-surface)",
                  // @ts-expect-error css var
                  "--tw-ring-color": "var(--c-ring)",
                }}
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium">パスワード</label>
              <input
                type="password"
                placeholder="••••••••"
                className="w-full border px-3 py-2.5 text-sm outline-none focus:ring-2"
                style={{
                  borderColor: "var(--c-border)",
                  borderRadius: "var(--c-radius)",
                  backgroundColor: "var(--c-surface)",
                  // @ts-expect-error css var
                  "--tw-ring-color": "var(--c-ring)",
                }}
              />
            </div>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-[var(--c-text-muted)]">
                <input type="checkbox" className="h-4 w-4 accent-[var(--c-primary)]" />
                ログイン状態を保持
              </label>
              <a className="font-medium" style={{ color: "var(--c-primary)" }} href="#">
                パスワードを忘れた
              </a>
            </div>

            <button
              className="mt-2 flex w-full items-center justify-center gap-2 rounded-[var(--c-radius)] py-3 text-sm font-semibold"
              style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
            >
              ログイン <ArrowRight className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-3 py-1 text-xs text-[var(--c-text-muted)]">
              <span className="h-px flex-1 bg-[var(--c-border)]" />
              または
              <span className="h-px flex-1 bg-[var(--c-border)]" />
            </div>

            <button
              className="flex w-full items-center justify-center gap-2 rounded-[var(--c-radius)] border py-3 text-sm font-semibold"
              style={{ borderColor: "var(--c-border)", color: "var(--c-text)" }}
            >
              <IdCard className="h-4 w-4" style={{ color: "var(--c-accent)" }} />
              マイナンバーカードでログイン
            </button>
          </div>

          <p className="mt-8 flex items-center justify-center gap-1.5 text-center text-xs text-[var(--c-text-muted)]">
            <Lock className="h-3 w-3" />
            この接続は暗号化されています
          </p>
        </div>
      </div>
    </div>
  )
}
