export type SSLState =
  | "ok"
  | "warning"
  | "critical"
  | "invalid"
  | "no_data"
  | "http"

export const sslLabels = {
  http: "Без SSL",
  ok: "SSL дійсний",
  warning: "Попередження",
  critical: "Критично",
  invalid: "Недійсний",
  no_data: "Немає даних",
} as const satisfies Record<SSLState, string>

export const sslMeta: Record<SSLState, { label: string }> = {
  critical: { label: "🔥 Критично" },
  warning: { label: "⚠ Попередження" },
  invalid: { label: "❌ Недійсний" },
  ok: { label: "SSL дійсний" },
  no_data: { label: "Немає даних" },
  http: { label: "Без SSL (HTTP)" },
} as const