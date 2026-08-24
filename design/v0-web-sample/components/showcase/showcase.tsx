"use client"

import { useState } from "react"
import { CONCEPTS, SCREENS, themeToStyle, type ConceptId, type ScreenId } from "@/lib/concepts"
import { LpScreen } from "./screens/lp-screen"
import { ChatScreen } from "./screens/chat-screen"
import { LoginScreen } from "./screens/login-screen"
import { AdminScreen } from "./screens/admin-screen"

export function Showcase() {
  const [conceptId, setConceptId] = useState<ConceptId>("sei")
  const [screen, setScreen] = useState<ScreenId>("lp")

  const concept = CONCEPTS.find((c) => c.id === conceptId)!

  return (
    <div className="flex min-h-svh flex-col bg-neutral-950 text-neutral-100 [font-family:var(--font-noto-sans),sans-serif]">
      {/* コントロールバー */}
      <header className="sticky top-0 z-30 border-b border-white/10 bg-neutral-950/95 backdrop-blur">
        <div className="mx-auto flex max-w-[1400px] flex-col gap-3 px-4 py-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md bg-white text-lg font-bold text-neutral-950">
              源
            </div>
            <div className="leading-tight">
              <p className="text-sm font-bold">源内 — ガバメントAI デザイン提案</p>
              <p className="text-xs text-neutral-400">Tri-tome / 3案比較プロトタイプ</p>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            {/* 案切り替え */}
            <div
              className="flex items-center gap-1 rounded-lg bg-white/5 p-1"
              role="tablist"
              aria-label="デザイン案の切り替え"
            >
              {CONCEPTS.map((c) => (
                <button
                  key={c.id}
                  role="tab"
                  aria-selected={c.id === conceptId}
                  onClick={() => setConceptId(c.id)}
                  className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    c.id === conceptId
                      ? "bg-white text-neutral-950"
                      : "text-neutral-300 hover:bg-white/10"
                  }`}
                >
                  <span
                    className="flex h-5 w-5 items-center justify-center rounded text-xs font-bold"
                    style={{
                      backgroundColor: c.theme.primary,
                      color: c.theme.primaryFg,
                    }}
                  >
                    {c.mark}
                  </span>
                  {c.id === "sei" ? "案A" : c.id === "chi" ? "案B" : "案C"}
                </button>
              ))}
            </div>

            {/* 画面切り替え */}
            <div
              className="flex items-center gap-1 overflow-x-auto rounded-lg bg-white/5 p-1"
              role="tablist"
              aria-label="画面の切り替え"
            >
              {SCREENS.map((s) => (
                <button
                  key={s.id}
                  role="tab"
                  aria-selected={s.id === screen}
                  onClick={() => setScreen(s.id)}
                  className={`whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    s.id === screen ? "bg-white/15 text-white" : "text-neutral-300 hover:bg-white/10"
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* 案の説明 */}
      <div className="border-b border-white/10 bg-neutral-900/60">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-2.5">
          <span className="text-sm font-bold text-white">{concept.name}</span>
          <span className="text-sm text-neutral-300">{concept.tagline}</span>
          <span className="hidden text-xs text-neutral-500 md:inline">— {concept.description}</span>
        </div>
      </div>

      {/* プレビュー領域 */}
      <main className="flex-1 bg-neutral-800 p-3 sm:p-6">
        <div className="mx-auto max-w-[1400px]">
          <div className="overflow-hidden rounded-xl border border-white/10 shadow-2xl">
            {/* ブラウザ風フレーム */}
            <div className="flex items-center gap-2 border-b border-black/5 bg-neutral-200 px-4 py-2.5">
              <div className="flex gap-1.5">
                <span className="h-3 w-3 rounded-full bg-neutral-400" />
                <span className="h-3 w-3 rounded-full bg-neutral-400" />
                <span className="h-3 w-3 rounded-full bg-neutral-400" />
              </div>
              <div className="mx-auto flex w-full max-w-md items-center justify-center rounded-md bg-white px-3 py-1 text-xs text-neutral-500">
                gennai.{concept.id}.example.jp
              </div>
            </div>

            {/* テーマ適用ラッパー */}
            <div
              style={themeToStyle(concept.theme)}
              className="bg-[var(--c-bg)] text-[var(--c-text)] [font-family:var(--font-body)]"
            >
              {screen === "lp" && <LpScreen />}
              {screen === "chat" && <ChatScreen />}
              {screen === "login" && <LoginScreen />}
              {screen === "admin" && <AdminScreen />}
            </div>
          </div>

          <p className="mx-auto mt-4 max-w-2xl text-center text-xs text-neutral-400 text-pretty">
            ※ 本文・数値はすべてデザイン確認用のダミーです。上部のタブで「案A/B/C」と「画面」を切り替えて比較できます。
          </p>
        </div>
      </main>
    </div>
  )
}
