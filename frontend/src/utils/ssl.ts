const normalizeSSL = (state?: string | null) => {
  if (!state) return "no_data"
  if (state === "http") return "http"
  return state
}

export const sslMeta = {
  critical: { label: "🔥 Критично", severity: "bad" },
  warning: { label: "⚠ Попередження", severity: "warn" },
  invalid: { label: "❌ Недійсний", severity: "bad" },
  ok: { label: "SSL OK", severity: "good" },
  no_data: { label: "Немає даних", severity: "warn" },
  http: { label: "Без SSL (HTTP)", severity: "warn" },
} as const