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

export const sslMeta: Record<SSLState, { label: string; severity: "good" | "warn" | "bad" }> = {
  critical: { label: "🔥 Критично", severity: "bad" },
  warning: { label: "⚠ Попередження", severity: "warn" },
  invalid: { label: "❌ Недійсний", severity: "bad" },
  ok: { label: "SSL дійсний", severity: "good" },
  no_data: { label: "Немає даних", severity: "warn" },
  http: { label: "Без SSL (HTTP)", severity: "warn" },
} as const