const allowed = ["critical", "warning", "invalid", "ok", "no_data", "http"]

export const normalizeSSL = (state?: string | null) => {
  if (!state || !allowed.includes(state)) return "no_data"
  return state
}

export const sslMeta = {
  critical: { label: "🔥 Критично", severity: "bad" },
  warning: { label: "⚠ Попередження", severity: "warn" },
  invalid: { label: "❌ Недійсний", severity: "bad" },
  ok: { label: "SSL дійсний", severity: "good" },
  no_data: { label: "Немає даних", severity: "warn" },
  http: { label: "Без SSL (HTTP)", severity: "warn" },
} as const