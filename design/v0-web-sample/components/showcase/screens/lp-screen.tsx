import {
  ShieldCheck,
  Database,
  GraduationCap,
  Server,
  Lock,
  FileSearch,
  ArrowRight,
  Check,
} from "lucide-react"

const features = [
  {
    icon: Server,
    title: "環境構築ワンストップ",
    body: "デジタル庁OSSをベースに、自治体ごとの要件へ最適化した基盤をセキュアに構築・運用。",
  },
  {
    icon: ShieldCheck,
    title: "自治体水準のセキュリティ",
    body: "LGWAN・ゼロトラストを前提とした設計と権限管理で、機微情報を守りながら生成AIを活用。",
  },
  {
    icon: Database,
    title: "庁内文書のRAG整備",
    body: "例規・要綱・過去回答をナレッジ化し、根拠付きの回答を返す検索拡張生成を導入支援。",
  },
  {
    icon: GraduationCap,
    title: "職員向け研修",
    body: "はじめての職員でも安心して使えるよう、実務に沿ったプロンプト研修とガイドラインを提供。",
  },
]

const stats = [
  { value: "78%", label: "文書作成時間の削減" },
  { value: "3週間", label: "最短導入リードタイム" },
  { value: "24/365", label: "運用監視体制" },
]

const useCases = [
  { title: "議会答弁の下書き", desc: "過去答弁と例規を参照し、根拠付きの草案を数分で。" },
  { title: "住民向け文書の平易化", desc: "専門用語を平易な表現へ。多言語のたたき台にも対応。" },
  { title: "例規・要綱の横断検索", desc: "出典リンク付きで該当条文を素早く提示。" },
  { title: "会議録の要約", desc: "長時間の議事を論点ごとに整理し要点を抽出。" },
]

export function LpScreen() {
  return (
    <div className="[&_h1]:[font-family:var(--font-heading)] [&_h2]:[font-family:var(--font-heading)] [&_h3]:[font-family:var(--font-heading)]">
      {/* ナビ */}
      <nav className="flex items-center justify-between border-b border-[var(--c-border)] px-6 py-4 lg:px-10">
        <div className="flex items-center gap-2.5">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-[calc(var(--c-radius)*0.6)] text-lg font-bold"
            style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
          >
            源
          </span>
          <span className="text-lg font-bold tracking-tight">源内</span>
          <span className="ml-1 hidden text-xs text-[var(--c-text-muted)] sm:inline">
            ガバメントAI
          </span>
        </div>
        <div className="hidden items-center gap-7 text-sm text-[var(--c-text-muted)] md:flex">
          <span>特長</span>
          <span>活用例</span>
          <span>セキュリティ</span>
          <span>導入の流れ</span>
        </div>
        <button
          className="rounded-[calc(var(--c-radius)*0.7)] px-4 py-2 text-sm font-semibold"
          style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
        >
          資料請求
        </button>
      </nav>

      {/* ヒーロー */}
      <section className="grid items-center gap-10 px-6 py-14 lg:grid-cols-2 lg:px-10 lg:py-20">
        <div>
          <span
            className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold"
            style={{ backgroundColor: "var(--c-primary-soft)", color: "var(--c-primary)" }}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            デジタル庁OSS「源内」導入支援
          </span>
          <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-balance lg:text-5xl">
            行政の現場に、
            <br />
            信頼できる生成AIを。
          </h1>
          <p className="mt-5 max-w-md text-base leading-relaxed text-[var(--c-text-muted)] text-pretty">
            源内は、自治体の実務に寄り添うガバメントAI。環境構築からセキュリティ、庁内文書の活用、職員研修までワンストップで支援します。
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button
              className="inline-flex items-center gap-2 rounded-[calc(var(--c-radius)*0.7)] px-5 py-3 text-sm font-semibold"
              style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
            >
              無料でデモを試す <ArrowRight className="h-4 w-4" />
            </button>
            <button
              className="rounded-[calc(var(--c-radius)*0.7)] border px-5 py-3 text-sm font-semibold"
              style={{ borderColor: "var(--c-border)", color: "var(--c-text)" }}
            >
              導入事例を見る
            </button>
          </div>
          <div className="mt-8 flex flex-wrap gap-6">
            {stats.map((s) => (
              <div key={s.label}>
                <p className="text-2xl font-bold" style={{ color: "var(--c-primary)" }}>
                  {s.value}
                </p>
                <p className="text-xs text-[var(--c-text-muted)]">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="relative">
          <div
            className="overflow-hidden border border-[var(--c-border)] shadow-xl"
            style={{ borderRadius: "calc(var(--c-radius) * 1.2)" }}
          >
            <img
              src="/images/gennai-hero.png"
              alt="源内を活用する自治体職員のイメージ"
              className="h-full w-full object-cover"
            />
          </div>
          <div
            className="absolute -bottom-5 -left-5 hidden max-w-[220px] items-center gap-3 border border-[var(--c-border)] bg-[var(--c-surface)] p-4 shadow-lg sm:flex"
            style={{ borderRadius: "var(--c-radius)" }}
          >
            <span
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
              style={{ backgroundColor: "var(--c-accent-soft)", color: "var(--c-accent)" }}
            >
              <Lock className="h-5 w-5" />
            </span>
            <p className="text-xs leading-snug text-[var(--c-text-muted)]">
              庁内データは外部学習に
              <span className="font-semibold text-[var(--c-text)]">利用されません</span>
            </p>
          </div>
        </div>
      </section>

      {/* 特長 */}
      <section className="bg-[var(--c-surface)] px-6 py-16 lg:px-10">
        <div className="mx-auto max-w-5xl">
          <p className="text-sm font-semibold" style={{ color: "var(--c-primary)" }}>
            FEATURES
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight lg:text-3xl">
            導入から定着まで、ワンストップで支援
          </h2>
          <div className="mt-10 grid gap-5 sm:grid-cols-2">
            {features.map((f) => (
              <div
                key={f.title}
                className="border border-[var(--c-border)] bg-[var(--c-bg)] p-6"
                style={{ borderRadius: "var(--c-radius)" }}
              >
                <span
                  className="flex h-11 w-11 items-center justify-center rounded-[calc(var(--c-radius)*0.8)]"
                  style={{ backgroundColor: "var(--c-primary-soft)", color: "var(--c-primary)" }}
                >
                  <f.icon className="h-5 w-5" />
                </span>
                <h3 className="mt-4 text-lg font-bold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[var(--c-text-muted)]">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 活用例 */}
      <section className="px-6 py-16 lg:px-10">
        <div className="mx-auto max-w-5xl">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-sm font-semibold" style={{ color: "var(--c-primary)" }}>
                USE CASES
              </p>
              <h2 className="mt-2 text-2xl font-bold tracking-tight lg:text-3xl">
                現場のこんな業務に
              </h2>
            </div>
            <FileSearch className="hidden h-8 w-8 text-[var(--c-text-muted)] sm:block" />
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-2">
            {useCases.map((u, i) => (
              <div
                key={u.title}
                className="flex items-start gap-4 border border-[var(--c-border)] p-5"
                style={{ borderRadius: "var(--c-radius)" }}
              >
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold"
                  style={{ backgroundColor: "var(--c-accent-soft)", color: "var(--c-accent)" }}
                >
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="font-bold">{u.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-[var(--c-text-muted)]">{u.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* セキュリティ帯 */}
      <section
        className="px-6 py-14 lg:px-10"
        style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
      >
        <div className="mx-auto flex max-w-5xl flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
          <div>
            <h2 className="text-2xl font-bold tracking-tight lg:text-3xl">
              セキュリティは、妥協しない。
            </h2>
            <ul className="mt-5 grid gap-2.5 text-sm sm:grid-cols-2">
              {[
                "LGWAN対応・閉域接続",
                "ロールベースのアクセス制御",
                "全操作の監査ログ保持",
                "国内リージョンでのデータ管理",
              ].map((t) => (
                <li key={t} className="flex items-center gap-2 opacity-95">
                  <Check className="h-4 w-4 shrink-0" />
                  {t}
                </li>
              ))}
            </ul>
          </div>
          <button
            className="shrink-0 rounded-[calc(var(--c-radius)*0.7)] bg-[var(--c-primary-fg)] px-6 py-3 text-sm font-bold"
            style={{ color: "var(--c-primary)" }}
          >
            セキュリティ資料をダウンロード
          </button>
        </div>
      </section>

      {/* CTA / フッター */}
      <footer className="bg-[var(--c-surface)] px-6 py-12 lg:px-10">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-4 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-balance">
            まずは、貴庁の課題からご相談ください
          </h2>
          <p className="max-w-md text-sm leading-relaxed text-[var(--c-text-muted)]">
            オンラインデモと導入相談を随時受け付けています。
          </p>
          <button
            className="mt-2 inline-flex items-center gap-2 rounded-[calc(var(--c-radius)*0.7)] px-6 py-3 text-sm font-semibold"
            style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
          >
            お問い合わせ <ArrowRight className="h-4 w-4" />
          </button>
          <p className="mt-6 text-xs text-[var(--c-text-muted)]">
            © 2026 Tri-tome Inc. 源内はガバメントAI導入支援サービスです。
          </p>
        </div>
      </footer>
    </div>
  )
}
