import {
  LayoutDashboard,
  Users,
  FileText,
  Shield,
  Settings,
  TrendingUp,
  MessageSquareText,
  Clock,
  CircleAlert,
  Search,
  Bell,
} from "lucide-react"

const nav = [
  { icon: LayoutDashboard, label: "ダッシュボード", active: true },
  { icon: Users, label: "利用者管理" },
  { icon: FileText, label: "ナレッジ文書" },
  { icon: Shield, label: "監査ログ" },
  { icon: Settings, label: "設定" },
]

const stats = [
  { icon: MessageSquareText, label: "今月の対話数", value: "12,480", delta: "+18%" },
  { icon: Users, label: "アクティブ職員", value: "342", delta: "+7%" },
  { icon: Clock, label: "平均削減時間/件", value: "23分", delta: "+4%" },
  { icon: CircleAlert, label: "要確認フラグ", value: "6", delta: "-2" },
]

const chart = [
  { d: "月", v: 62 },
  { d: "火", v: 78 },
  { d: "水", v: 54 },
  { d: "木", v: 88 },
  { d: "金", v: 96 },
  { d: "土", v: 22 },
  { d: "日", v: 14 },
]

const depts = [
  { name: "市民課", rate: 92 },
  { name: "総務課", rate: 74 },
  { name: "福祉課", rate: 61 },
  { name: "税務課", rate: 48 },
]

const logs = [
  { user: "田中 花子", dept: "市民課", action: "住民票の広域交付を照会", time: "10:24", tag: "正常" },
  { user: "佐藤 健", dept: "総務課", action: "議会答弁の下書きを生成", time: "10:11", tag: "正常" },
  { user: "鈴木 一郎", dept: "税務課", action: "外部 URL への添付を検知", time: "09:52", tag: "要確認" },
  { user: "高橋 美咲", dept: "福祉課", action: "要綱の横断検索", time: "09:37", tag: "正常" },
]

export function AdminScreen() {
  const max = Math.max(...chart.map((c) => c.v))

  return (
    <div className="flex min-h-[720px] [font-family:var(--font-body)]">
      {/* サイドバー */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-[var(--c-border)] bg-[var(--c-surface)] lg:flex">
        <div className="flex items-center gap-2.5 px-5 py-5">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-[calc(var(--c-radius)*0.6)] text-sm font-bold"
            style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
          >
            源
          </span>
          <div className="leading-tight">
            <p className="text-sm font-bold [font-family:var(--font-heading)]">源内 管理</p>
            <p className="text-[10px] text-[var(--c-text-muted)]">◯◯市役所</p>
          </div>
        </div>
        <nav className="mt-2 flex-1 space-y-1 px-3">
          {nav.map((n) => (
            <button
              key={n.label}
              className="flex w-full items-center gap-3 rounded-[calc(var(--c-radius)*0.7)] px-3 py-2.5 text-sm font-medium"
              style={
                n.active
                  ? { backgroundColor: "var(--c-primary-soft)", color: "var(--c-primary)" }
                  : { color: "var(--c-text-muted)" }
              }
            >
              <n.icon className="h-4 w-4" />
              {n.label}
            </button>
          ))}
        </nav>
        <div className="m-3 rounded-[var(--c-radius)] p-4" style={{ backgroundColor: "var(--c-primary-soft)" }}>
          <Shield className="h-5 w-5" style={{ color: "var(--c-primary)" }} />
          <p className="mt-2 text-xs font-semibold" style={{ color: "var(--c-primary)" }}>
            セキュリティ状態: 良好
          </p>
          <p className="mt-1 text-[11px] text-[var(--c-text-muted)]">全システム正常稼働中</p>
        </div>
      </aside>

      {/* メイン */}
      <div className="flex-1 bg-[var(--c-bg)]">
        {/* ヘッダー */}
        <header className="flex items-center justify-between border-b border-[var(--c-border)] px-6 py-3.5">
          <h1 className="text-lg font-bold [font-family:var(--font-heading)]">ダッシュボード</h1>
          <div className="flex items-center gap-3">
            <div
              className="hidden items-center gap-2 border px-3 py-1.5 sm:flex"
              style={{ borderColor: "var(--c-border)", borderRadius: "var(--c-radius)" }}
            >
              <Search className="h-3.5 w-3.5 text-[var(--c-text-muted)]" />
              <span className="text-xs text-[var(--c-text-muted)]">検索…</span>
            </div>
            <button className="relative text-[var(--c-text-muted)]" aria-label="通知">
              <Bell className="h-5 w-5" />
              <span
                className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full"
                style={{ backgroundColor: "var(--c-accent)" }}
              />
            </button>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--c-surface2)] text-xs font-bold">
              管
            </span>
          </div>
        </header>

        <div className="space-y-6 p-6">
          {/* 統計カード */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((s) => (
              <div
                key={s.label}
                className="border border-[var(--c-border)] bg-[var(--c-surface)] p-4"
                style={{ borderRadius: "var(--c-radius)" }}
              >
                <div className="flex items-center justify-between">
                  <span
                    className="flex h-9 w-9 items-center justify-center rounded-[calc(var(--c-radius)*0.7)]"
                    style={{ backgroundColor: "var(--c-primary-soft)", color: "var(--c-primary)" }}
                  >
                    <s.icon className="h-4 w-4" />
                  </span>
                  <span className="text-xs font-semibold" style={{ color: "var(--c-accent)" }}>
                    {s.delta}
                  </span>
                </div>
                <p className="mt-3 text-2xl font-bold">{s.value}</p>
                <p className="text-xs text-[var(--c-text-muted)]">{s.label}</p>
              </div>
            ))}
          </div>

          {/* グラフ + 部署別 */}
          <div className="grid gap-4 lg:grid-cols-3">
            {/* 週間対話数 */}
            <div
              className="border border-[var(--c-border)] bg-[var(--c-surface)] p-5 lg:col-span-2"
              style={{ borderRadius: "var(--c-radius)" }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" style={{ color: "var(--c-primary)" }} />
                  <h3 className="text-sm font-bold">週間の対話数</h3>
                </div>
                <span className="text-xs text-[var(--c-text-muted)]">直近7日間</span>
              </div>
              <div className="mt-6 flex h-44 items-stretch justify-between gap-3">
                {chart.map((c) => (
                  <div key={c.d} className="flex flex-1 flex-col items-center gap-2">
                    <div className="flex w-full flex-1 items-end">
                      <div
                        className="w-full rounded-t-[calc(var(--c-radius)*0.5)]"
                        style={{
                          height: `${(c.v / max) * 100}%`,
                          backgroundColor: "var(--c-primary)",
                        }}
                      />
                    </div>
                    <span className="text-[11px] text-[var(--c-text-muted)]">{c.d}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* 部署別利用率 */}
            <div
              className="border border-[var(--c-border)] bg-[var(--c-surface)] p-5"
              style={{ borderRadius: "var(--c-radius)" }}
            >
              <h3 className="text-sm font-bold">部署別 利用率</h3>
              <div className="mt-5 space-y-4">
                {depts.map((d) => (
                  <div key={d.name}>
                    <div className="mb-1.5 flex items-center justify-between text-xs">
                      <span>{d.name}</span>
                      <span className="font-semibold text-[var(--c-text-muted)]">{d.rate}%</span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-[var(--c-surface2)]">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${d.rate}%`, backgroundColor: "var(--c-accent)" }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 監査ログ */}
          <div
            className="border border-[var(--c-border)] bg-[var(--c-surface)]"
            style={{ borderRadius: "var(--c-radius)" }}
          >
            <div className="flex items-center justify-between border-b border-[var(--c-border)] px-5 py-3.5">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4" style={{ color: "var(--c-primary)" }} />
                <h3 className="text-sm font-bold">最近の監査ログ</h3>
              </div>
              <button className="text-xs font-medium" style={{ color: "var(--c-primary)" }}>
                すべて表示
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-xs text-[var(--c-text-muted)]">
                    <th className="px-5 py-2.5 font-medium">職員</th>
                    <th className="px-5 py-2.5 font-medium">操作内容</th>
                    <th className="px-5 py-2.5 font-medium">時刻</th>
                    <th className="px-5 py-2.5 font-medium">状態</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((l, i) => (
                    <tr key={i} className="border-t border-[var(--c-border)]">
                      <td className="px-5 py-3">
                        <p className="font-medium">{l.user}</p>
                        <p className="text-xs text-[var(--c-text-muted)]">{l.dept}</p>
                      </td>
                      <td className="px-5 py-3 text-[var(--c-text-muted)]">{l.action}</td>
                      <td className="px-5 py-3 text-[var(--c-text-muted)]">{l.time}</td>
                      <td className="px-5 py-3">
                        <span
                          className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
                          style={
                            l.tag === "要確認"
                              ? { backgroundColor: "var(--c-accent-soft)", color: "var(--c-accent)" }
                              : { backgroundColor: "var(--c-primary-soft)", color: "var(--c-primary)" }
                          }
                        >
                          {l.tag}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
