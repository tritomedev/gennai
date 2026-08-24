"use client"

import { useState } from "react"
import {
  Plus,
  Send,
  Paperclip,
  BookOpen,
  Sparkles,
  MessageSquare,
  Search,
  Settings,
  FileText,
  ThumbsUp,
  ThumbsDown,
  Copy,
} from "lucide-react"

type Msg = { role: "user" | "ai"; text: string; sources?: string[] }

const initialMessages: Msg[] = [
  {
    role: "user",
    text: "住民票の広域交付について、根拠となる条文を教えてください。",
  },
  {
    role: "ai",
    text: "住民票の広域交付は、住民基本台帳法第12条の4に基づく制度です。本人または同一世帯員が、住所地以外の市区町村窓口でも住民票の写しを請求できます。請求時には本人確認書類（マイナンバーカード等）の提示が必要です。",
    sources: ["住民基本台帳法 第12条の4", "総務省 事務処理要領 3-2", "庁内FAQ: 広域交付の窓口対応"],
  },
]

const history = [
  { title: "住民票の広域交付について", active: true },
  { title: "議会答弁の下書き作成" },
  { title: "要綱の改正点まとめ" },
  { title: "会議録の要約(9/12)" },
  { title: "多言語案内文の作成" },
]

const suggestions = [
  "手数料の金額は？",
  "必要な本人確認書類は？",
  "代理人でも請求できますか？",
]

export function ChatScreen() {
  const [messages, setMessages] = useState<Msg[]>(initialMessages)
  const [input, setInput] = useState("")

  function send(text: string) {
    const t = text.trim()
    if (!t) return
    setMessages((m) => [
      ...m,
      { role: "user", text: t },
      {
        role: "ai",
        text: "（デモ応答）ご質問ありがとうございます。庁内ナレッジと関連例規を参照し、出典付きで回答します。実際の環境では、貴庁の文書に基づいた根拠付きの回答が表示されます。",
        sources: ["庁内ナレッジベース", "関連例規データベース"],
      },
    ])
    setInput("")
  }

  return (
    <div className="flex h-[720px] max-h-[80vh] [font-family:var(--font-body)]">
      {/* サイドバー */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-[var(--c-border)] bg-[var(--c-surface)] md:flex">
        <div className="flex items-center gap-2 px-4 py-4">
          <span
            className="flex h-8 w-8 items-center justify-center rounded-[calc(var(--c-radius)*0.6)] text-sm font-bold"
            style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
          >
            源
          </span>
          <span className="font-bold [font-family:var(--font-heading)]">源内</span>
        </div>
        <div className="px-3">
          <button
            className="flex w-full items-center justify-center gap-2 rounded-[calc(var(--c-radius)*0.7)] px-3 py-2.5 text-sm font-semibold"
            style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
          >
            <Plus className="h-4 w-4" /> 新しい会話
          </button>
        </div>
        <div className="mt-4 flex items-center gap-2 px-4 text-xs text-[var(--c-text-muted)]">
          <Search className="h-3.5 w-3.5" /> 履歴
        </div>
        <nav className="mt-2 flex-1 space-y-1 overflow-y-auto px-3">
          {history.map((h) => (
            <button
              key={h.title}
              className="flex w-full items-center gap-2 rounded-[calc(var(--c-radius)*0.6)] px-3 py-2 text-left text-sm"
              style={
                h.active
                  ? { backgroundColor: "var(--c-primary-soft)", color: "var(--c-primary)" }
                  : { color: "var(--c-text-muted)" }
              }
            >
              <MessageSquare className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{h.title}</span>
            </button>
          ))}
        </nav>
        <div className="border-t border-[var(--c-border)] px-3 py-3">
          <button className="flex w-full items-center gap-2 rounded-[calc(var(--c-radius)*0.6)] px-3 py-2 text-sm text-[var(--c-text-muted)]">
            <Settings className="h-4 w-4" /> 設定
          </button>
          <div className="mt-1 flex items-center gap-2 px-3 py-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--c-surface2)] text-xs font-bold">
              田
            </span>
            <div className="leading-tight">
              <p className="text-xs font-semibold">田中 花子</p>
              <p className="text-[10px] text-[var(--c-text-muted)]">市民課</p>
            </div>
          </div>
        </div>
      </aside>

      {/* メイン */}
      <div className="flex flex-1 flex-col bg-[var(--c-bg)]">
        <header className="flex items-center justify-between border-b border-[var(--c-border)] px-5 py-3">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold [font-family:var(--font-heading)]">
              住民票の広域交付について
            </span>
            <span
              className="rounded-full px-2 py-0.5 text-[10px] font-semibold"
              style={{ backgroundColor: "var(--c-accent-soft)", color: "var(--c-accent)" }}
            >
              RAG: 庁内文書
            </span>
          </div>
          <span className="text-xs text-[var(--c-text-muted)]">GPT-4o 相当 / 国内リージョン</span>
        </header>

        {/* メッセージ */}
        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-6">
          {messages.map((m, i) => (
            <div key={i} className={`flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
              {m.role === "ai" && (
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold"
                  style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
                >
                  源
                </span>
              )}
              <div className={`max-w-[78%] ${m.role === "user" ? "order-first" : ""}`}>
                <div
                  className="px-4 py-3 text-sm leading-relaxed"
                  style={
                    m.role === "user"
                      ? {
                          backgroundColor: "var(--c-primary)",
                          color: "var(--c-primary-fg)",
                          borderRadius: "var(--c-radius)",
                        }
                      : {
                          backgroundColor: "var(--c-surface)",
                          border: "1px solid var(--c-border)",
                          borderRadius: "var(--c-radius)",
                        }
                  }
                >
                  {m.text}
                  {m.sources && (
                    <div className="mt-3 border-t border-[var(--c-border)] pt-3">
                      <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-[var(--c-text-muted)]">
                        <BookOpen className="h-3.5 w-3.5" /> 参照した出典
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {m.sources.map((s) => (
                          <span
                            key={s}
                            className="inline-flex items-center gap-1 rounded-[calc(var(--c-radius)*0.6)] px-2 py-1 text-[11px]"
                            style={{ backgroundColor: "var(--c-surface2)", color: "var(--c-text)" }}
                          >
                            <FileText className="h-3 w-3" style={{ color: "var(--c-accent)" }} />
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                {m.role === "ai" && (
                  <div className="mt-2 flex items-center gap-3 text-[var(--c-text-muted)]">
                    <button aria-label="良い回答"><ThumbsUp className="h-3.5 w-3.5" /></button>
                    <button aria-label="悪い回答"><ThumbsDown className="h-3.5 w-3.5" /></button>
                    <button aria-label="コピー"><Copy className="h-3.5 w-3.5" /></button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* サジェスト */}
          <div className="flex flex-wrap gap-2 pl-11">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border px-3 py-1.5 text-xs"
                style={{ borderColor: "var(--c-border)", color: "var(--c-primary)" }}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* 入力欄 */}
        <div className="border-t border-[var(--c-border)] px-5 py-4">
          <div
            className="flex items-end gap-2 border p-2"
            style={{ borderColor: "var(--c-border)", borderRadius: "var(--c-radius)", backgroundColor: "var(--c-surface)" }}
          >
            <button className="p-2 text-[var(--c-text-muted)]" aria-label="ファイル添付">
              <Paperclip className="h-5 w-5" />
            </button>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing && e.keyCode !== 229) {
                  e.preventDefault()
                  send(input)
                }
              }}
              rows={1}
              placeholder="源内に質問する… (庁内文書を参照して回答します)"
              className="max-h-32 flex-1 resize-none bg-transparent py-2 text-sm outline-none placeholder:text-[var(--c-text-muted)]"
            />
            <button
              onClick={() => send(input)}
              className="flex h-9 w-9 items-center justify-center rounded-[calc(var(--c-radius)*0.7)]"
              style={{ backgroundColor: "var(--c-primary)", color: "var(--c-primary-fg)" }}
              aria-label="送信"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-[11px] text-[var(--c-text-muted)]">
            <Sparkles className="h-3 w-3" />
            生成AIの回答には誤りが含まれる場合があります。重要な判断は出典をご確認ください。
          </p>
        </div>
      </div>
    </div>
  )
}
