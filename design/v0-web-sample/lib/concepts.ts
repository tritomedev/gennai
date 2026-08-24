export type ConceptId = "sei" | "chi" | "yui"

export type ConceptTheme = {
  /** wrapper CSS custom properties */
  bg: string
  surface: string
  surface2: string
  text: string
  textMuted: string
  primary: string
  primaryFg: string
  primarySoft: string
  accent: string
  accentSoft: string
  border: string
  ring: string
  radius: string
  fontHeading: string
  fontBody: string
}

export type Concept = {
  id: ConceptId
  /** 短い記号名 */
  mark: string
  /** 案名 */
  name: string
  /** キャッチ */
  tagline: string
  /** 方向性の説明 */
  description: string
  theme: ConceptTheme
}

const SANS = "var(--font-noto-sans), system-ui, sans-serif"
const SERIF = "var(--font-noto-serif), serif"
const GEIST = "var(--font-geist), var(--font-noto-sans), sans-serif"

export const CONCEPTS: Concept[] = [
  {
    id: "sei",
    mark: "政",
    name: "案A クラシック・オーソリティ",
    tagline: "格式と信頼を宿す、行政の正統",
    description:
      "濃紺と明朝体を基調に、公文書のような端正さと権威を表現。角を抑えた堅牢なレイアウトで、意思決定層に安心感を与える方向性。",
    theme: {
      bg: "#ffffff",
      surface: "#f6f8fb",
      surface2: "#eceff5",
      text: "#0e1b30",
      textMuted: "#54637a",
      primary: "#173e7c",
      primaryFg: "#ffffff",
      primarySoft: "#e5ebf5",
      accent: "#1e5fae",
      accentSoft: "#dde8f6",
      border: "#d3dbe8",
      ring: "#173e7c",
      radius: "4px",
      fontHeading: SERIF,
      fontBody: SANS,
    },
  },
  {
    id: "chi",
    mark: "知",
    name: "案B クリーンテック",
    tagline: "先進性を、澄んだ余白で語る",
    description:
      "明るいブルーとシアンのアクセント、広い余白と丸みで、生成AIらしい先進性と軽やかさを表現。UIの操作性を最優先にしたモダンな方向性。",
    theme: {
      bg: "#f6fafd",
      surface: "#ffffff",
      surface2: "#eef6fc",
      text: "#0a1f33",
      textMuted: "#5a7087",
      primary: "#0a6ce0",
      primaryFg: "#ffffff",
      primarySoft: "#e2f0fd",
      accent: "#0aa5c4",
      accentSoft: "#d8f3f8",
      border: "#dbe7f1",
      ring: "#0a6ce0",
      radius: "14px",
      fontHeading: GEIST,
      fontBody: SANS,
    },
  },
  {
    id: "yui",
    mark: "結",
    name: "案C 親しみやすい公共",
    tagline: "誰もが迷わず使える、やさしい窓口",
    description:
      "やわらかなインディゴと温かみのあるアクセント、大きめの文字と余裕ある余白で、現場職員が日常的に使いやすい親しみのある方向性。",
    theme: {
      bg: "#f4f6fb",
      surface: "#ffffff",
      surface2: "#eaeffb",
      text: "#1b2440",
      textMuted: "#61708c",
      primary: "#3a56c5",
      primaryFg: "#ffffff",
      primarySoft: "#e6ebfb",
      accent: "#e8770c",
      accentSoft: "#fcecd8",
      border: "#dde3f0",
      ring: "#3a56c5",
      radius: "20px",
      fontHeading: SANS,
      fontBody: SANS,
    },
  },
]

export function themeToStyle(t: ConceptTheme): React.CSSProperties {
  return {
    // @ts-expect-error CSS custom properties
    "--c-bg": t.bg,
    "--c-surface": t.surface,
    "--c-surface2": t.surface2,
    "--c-text": t.text,
    "--c-text-muted": t.textMuted,
    "--c-primary": t.primary,
    "--c-primary-fg": t.primaryFg,
    "--c-primary-soft": t.primarySoft,
    "--c-accent": t.accent,
    "--c-accent-soft": t.accentSoft,
    "--c-border": t.border,
    "--c-ring": t.ring,
    "--c-radius": t.radius,
    "--font-heading": t.fontHeading,
    "--font-body": t.fontBody,
  }
}

export type ScreenId = "lp" | "chat" | "login" | "admin"

export const SCREENS: { id: ScreenId; label: string }[] = [
  { id: "lp", label: "紹介・LP" },
  { id: "chat", label: "AIチャット" },
  { id: "login", label: "ログイン" },
  { id: "admin", label: "管理画面" },
]
