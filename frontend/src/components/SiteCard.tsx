import { sslMeta, sslLabels } from "../utils/ssl"
import type { SiteStatus, SSLState} from "../types/api";
import { useState, useEffect, useMemo, useRef } from "react";
import api from "../api/axios";
import StatusBadge from "./StatusBadge";
import type { Check } from "../types/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

interface Props {
  site_id: string;
  name: string;
  url: string;
  last_status: SiteStatus | null;
  uptime_24h: number;
  uptime_7d: number;
  uptime_30d: number;
  check_interval: number;
  last_checked_at: string | null;
  archived?: boolean;
  ssl_state?: SSLState | null;
  ssl_days_left?: number | null;
  p95_latency?: number;
  error_rate?: number;
  health?: "ok" | "warning" | "critical" | "no_data";
  onDeleted?: () => void;
  onReactivated?: () => void;
}

const statusLabels: Record<SiteStatus, string> = {
  UP: "Працює",
  DOWN: "Недоступний",
  TIMEOUT: "Таймаут",
  ERROR: "Помилка",
}

const healthLabels = {
  critical: "🔴 Критично",
  warning: "🟡 Попередження",
  ok: "🟢 Нормально",
  no_data: "⚪ Немає даних",
}

export default function SiteCard({
  site_id,
  name,
  url,
  last_status,
  uptime_24h,
  uptime_7d,
  uptime_30d,
  check_interval,
  last_checked_at,
  archived,
  onDeleted,
  onReactivated,
  ssl_state,
  ssl_days_left,
  p95_latency,
  error_rate,
  health,
}: Props) {

  const [expanded, setExpanded] = useState(false);
  const [rawData, setRawData] = useState<Check[]>([]);
  const [loading, setLoading] = useState(false);
  const [range, setRange] = useState<"24h" | "7d" | "30d">("24h");
  const [intervalEdit, setIntervalEdit] = useState(check_interval);
  const [debouncedRange, setDebouncedRange] = useState<"24h" | "7d" | "30d">("24h")
  const [exporting, setExporting] = useState(false)

const formatDate = (d: string | null) => {
  if (!d) return "—"
  const date = new Date(d)
  if (isNaN(date.getTime())) return "—"

  return date.toLocaleString("uk-UA", {
    timeZone: "Europe/Kyiv",
  })
}

const isHttp = url.startsWith("http://")

const sslState = ssl_state ?? "no_data"

const sslLabel = sslLabels[sslState] ?? "Немає даних"

const cacheRef = useRef<Map<string, Check[]>>(new Map())

useEffect(() => {
  const t = setTimeout(() => setDebouncedRange(range), 300)
  return () => clearTimeout(t)
}, [range])

const requestIdRef = useRef(0)

useEffect(() => {
  if (!expanded) return;

  const key = `${site_id}_${debouncedRange}`

  const cached = cacheRef.current.get(key)
  if (cached) {
  setRawData(cached)
  return
}

  const controller = new AbortController()
  const requestId = ++requestIdRef.current

  setLoading(true)
  setRawData([])

  api.get(`/dashboard/site/${site_id}`, {
    params: { range: debouncedRange },
    signal: controller.signal
  })
    .then(res => {
      if (requestId !== requestIdRef.current) return

      const data = Array.isArray(res.data) ? res.data : []
      cacheRef.current.set(key, data)
      setRawData(data)
    })
    .catch(err => {
        if (controller.signal.aborted) return
        if (requestId !== requestIdRef.current) return
        setRawData([])
    })
    .finally(() => {
      if (requestId === requestIdRef.current) {
        setLoading(false)
      }
    })

  return () => controller.abort()

}, [expanded, site_id, debouncedRange])

const safeData = Array.isArray(rawData) ? rawData : []
const chartData = useMemo(() => {
  if (safeData.length === 0) return []

  const result = []

  for (const c of safeData.slice(-1000)) {
    if (!c) continue

    const t = new Date(c.checked_at ?? "")
    if (isNaN(t.getTime())) continue

    const rt = c.avg_response_time_ms ?? c.response_time_ms

    result.push({
      time: t.getTime(),
      timeFormatted: t.toLocaleTimeString("uk-UA", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZone: "Europe/Kyiv"
      }),
      response_time: typeof rt === "number" && isFinite(rt) ? rt : null,
      status: c.status ?? null,
      ssl_state: c.ssl_state ?? "no_data",
      ssl_days_left: c.ssl_days_left ?? null,
      health: c.health ?? "no_data",
    })
  }

  return result
}, [safeData])

  const threshold = 500;

  const updateInterval = async () => {
  try {
    await api.patch(`/sites/${site_id}/interval`, {
      check_interval: intervalEdit,
    })

    alert("Інтервал оновлено")
  } catch {
    alert("Не вдалося оновити інтервал")
  }
};

const average = useMemo(() => {
  if (!chartData || chartData.length === 0) return null

  let sum = 0
  let count = 0

  for (const v of chartData) {
    if (v.response_time != null) {
      sum += v.response_time
      count++
    }
  }

  return count ? sum / count : null
}, [chartData])

const clearCache = () => {
  for (const key of cacheRef.current.keys()) {
    if (key.startsWith(site_id)) {
      cacheRef.current.delete(key)
    }
  }
}

  const handleArchive = async () => {
  if (!confirm("Архівувати сайт?")) return;
  await api.post(`/sites/${site_id}/deactivate`);
  clearCache()
  onDeleted?.();
};

const handleReactivate = async () => {
  await api.post(`/sites/${site_id}/reactivate`);
  clearCache()
  onReactivated?.();
};

const handleExport = async () => {
  if (exporting) return

  setExporting(true)

  try {
    const response = await api.get(`/export/site/${site_id}`, {
      params: { range: debouncedRange },
      responseType: "blob",
      timeout: 20000,
    })

    const blob = new Blob([response.data], { type: "text/csv" })
    const link = document.createElement("a")
    const urlObj = URL.createObjectURL(blob)

    link.href = urlObj
    link.setAttribute("download", `${name}_${debouncedRange}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()

    URL.revokeObjectURL(urlObj)

  } catch (e: any) {
    console.error(e)

    if (e?.response?.status === 500) {
      alert("Помилка сервера під час експорту")
    } else {
      alert("Експорт не вдався")
    }
  } finally {
    setExporting(false)
  }
}

  return (
    <div
className={`rounded-xl p-6 shadow border-2 transition ${
archived
    ? "border-gray-400 opacity-70"
    : health === "critical"
    ? "border-red-600"
    : health === "warning"
    ? "border-yellow-400"
    : health === "no_data"
    ? "border-gray-400"
    : "border-gray-300"
}`}
>
  <div className="flex items-center gap-2">
  <StatusBadge status={last_status} />

<span className="text-xs font-semibold">
  {health === "critical" && "🔴 Критично"}
  {health === "warning" && "🟡 Попередження"}
  {health === "ok" && "🟢 Нормально"}
  {health === "no_data" && "⚪ Немає даних"}
</span>
</div>

<div className="text-xs text-gray-500 mt-1">
  {isHttp ? (
    <span className="text-orange-600">🌐 HTTP (без SSL)</span>
  ) : (
    <>🔐 SSL: {sslLabel}</>
  )}
</div>
      {/* HEADER */}
      <div className="flex justify-between items-start">
        <div>
          <div className="font-semibold text-lg">{name}</div>
          <div className="text-sm text-gray-500">{url}</div>

          <div className="text-xs text-gray-400 mt-1 flex items-center gap-2">
            Кожні
            <input
              type="number"
              value={intervalEdit}
              onChange={(e) => setIntervalEdit(Number(e.target.value))}
              className="w-16 border rounded px-1 py-0.5 text-xs"
            />
            секунд
            <button
              onClick={updateInterval}
              className="px-2 py-0.5 bg-blue-600 text-white rounded text-xs"
            >
              Зберегти
            </button>
            · Остання перевірка: {formatDate(last_checked_at)}
          </div>
        </div>
        <div className="flex gap-2 flex-wrap mt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="px-3 py-1 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100"
          >
            {expanded ? "Приховати" : "Деталі"}
          </button>
            <button
            disabled={exporting}
  onClick={handleExport}
  className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
>
  {exporting ? "Експорт..." : "Експорт CSV"}
</button>
          {archived ? (
            <button
              onClick={handleReactivate}
              className="px-3 py-1 bg-green-50 text-green-700 rounded-md hover:bg-green-100"
            >
              Ре-активувати
            </button>
          ) : (
            <button
              onClick={handleArchive}
              className="px-3 py-1 bg-red-50 text-red-600 rounded-md hover:bg-red-100"
            >
              Архівувати
            </button>
          )}
        </div>
      </div>
<div className="grid grid-cols-3 gap-6 text-sm mt-4">
  <Uptime label="24г" value={uptime_24h} />
  <Uptime label="7д" value={uptime_7d} />
  <Uptime label="30д" value={uptime_30d} />
</div>

<div className="grid grid-cols-2 gap-6 text-sm mt-4">
  <div>
    <div className="text-xs text-gray-400">
     p95 latency (95% запитів швидше цього значення)
    </div>
    <div className="font-semibold">
      {typeof p95_latency === "number" ? `${Math.round(p95_latency)} ms` : "—"}
    </div>
  </div>

<div>
  <div className="text-gray-500">Error rate</div>

  {typeof error_rate === "number" ? (
    <div
      className={`font-semibold ${
        error_rate > 10
          ? "text-red-600"
          : error_rate > 2
          ? "text-yellow-600"
          : "text-green-600"
      }`}
    >
      {error_rate.toFixed(2)}%
  </div>
) : (
  <div className="text-gray-400">—</div>
)}
</div>
</div>

{expanded && (
  <div className="space-y-1 text-xs text-gray-500">

<div className="text-xs text-gray-400 italic">
  Стан формується з HTTP, SSL та помилок
</div>

<div className="flex gap-2 mt-4 text-sm">
  {["24h", "7d", "30d"].map(r => (
    <button
      key={r}
      onClick={() => setRange(r as "24h" | "7d" | "30d")}
      className={`px-3 py-1 rounded-md ${
        range === r ? "bg-blue-600 text-white" : "bg-gray-200"
      }`}
    >
      {r}
    </button>
  ))}
</div>

    <div className="mt-4 h-48">
      {loading ? (
        <div className="text-center text-gray-500 mt-20">
          Завантаження...
        </div>
      ) : chartData.length === 0 ? (
        <div className="text-center text-gray-500 mt-20">
          Немає даних
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%" minWidth={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
            dataKey="time"
            tickFormatter={(v) => {
            const d = new Date(v)
            return range === "24h"
            ? d.toLocaleTimeString("uk-UA", { hour: '2-digit', minute: '2-digit', timeZone: "Europe/Kyiv" })
            : d.toLocaleDateString("uk-UA", { day: '2-digit', month: '2-digit', timeZone: "Europe/Kyiv" })
            }}
            />
           <YAxis
  domain={[
    0,
    (dataMax: number) =>
      Number.isFinite(dataMax) ? dataMax * 1.2 : 1000
  ]}
/>



            <Tooltip
    content={({ active, payload }) => {
if (!active || !Array.isArray(payload) || payload.length === 0) return null

const p = payload[0]?.payload
if (!p || typeof p !== "object") return null

const pointState = p.ssl_state
const isHttp = pointState === "http"

const pointMeta = !isHttp
  ? sslMeta[pointState as keyof typeof sslMeta] ?? {
      label: "Невідомо",
      severity: "warn"
    }
  : null

const healthKey = (p.health ?? "no_data") as keyof typeof healthLabels

    return (
      <div className="bg-white p-2 border rounded shadow text-xs">
        <div>
        {p.timeFormatted}
        </div>

        <div>⏱ {p.response_time != null ? `${p.response_time} ms` : "—"}</div>

        <div>
          Статус: {p.status ? (statusLabels[p.status as keyof typeof statusLabels] ?? "—") : "—"}
        </div>

        {!isHttp && (
  <div className="font-medium">
    {pointMeta?.label}
  </div>
)}

        <div>Здоров'я: {healthLabels[healthKey] ?? "—"}</div>

       {!isHttp && p.ssl_days_left != null && (
  <div>
    {p.ssl_days_left <= 0
      ? "Термін дії SSL-сертифікату закінчився"
      : `Термін дії SSL-сертифікату закінчується через: ${p.ssl_days_left} днів`}
  </div>
)}
    </div>
    );
  }}
/>

            {average != null && (
  <ReferenceLine y={average} stroke="orange" strokeDasharray="4 4" />
)}
            <ReferenceLine y={threshold} stroke="red" strokeDasharray="2 2" />

<Line
  dataKey="response_time"
  stroke="#2563eb"
  dot={(props) => {
    const { payload } = props
    if (!payload) return false

const health = payload.health ?? "no_data"

const color =
  health === "critical"
    ? "#dc2626"
    : health === "warning"
    ? "#f59e0b"
    : health === "ok"
    ? "#16a34a"
    : "#9ca3af"

const colorMap = {
  critical: "#dc2626",
  warning: "#f59e0b",
  ok: "#16a34a",
  no_data: "#9ca3af"
}
return (
      <circle
        r={3}
        fill={color}
      />
    )
  }}
/>
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  </div>
)}
    </div>
  );
}

function Uptime({ label, value }: { label: string; value: number }) {
  let color = "text-gray-700";
  if (!Number.isFinite(value)) {
  return (
    <div>
      <div className="text-gray-500">uptime ({label})</div>
      <div className="text-gray-400">—</div>
    </div>
  )
}
  if (value < 90) color = "text-red-600";
  else if (value < 97) color = "text-yellow-600";
  else color = "text-green-600";

  return (
    <div>
      <div className="text-gray-500">uptime ({label})</div>
      <div className={`font-semibold ${color}`}>
        {Number.isFinite(value) ? value.toFixed(2) : "—"}%
      </div>
    </div>
  );
}