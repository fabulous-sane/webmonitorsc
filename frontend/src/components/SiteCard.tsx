import type { SiteStatus, SSLState, SSLSeverity } from "../types/api";
import { useState, useEffect, useMemo } from "react";
import api from "../api/axios";
import { isProblem } from "../types/status";
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
  ssl_severity?: SSLSeverity;
  p95_latency?: number
  error_rate?: number
  health?: "healthy" | "warning" | "critical"
  onDeleted?: () => void;
  onReactivated?: () => void;
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
  ssl_severity,
  p95_latency,
  error_rate,
  health,
}: Props) {

  const [expanded, setExpanded] = useState(false);
  const [rawData, setRawData] = useState<Check[]>([]);
  const [loading, setLoading] = useState(false);
  const [range, setRange] = useState<"24h" | "7d" | "30d">("24h");
  const [intervalEdit, setIntervalEdit] = useState(check_interval);
  const state = ssl_state
  const isHttp = ssl_state === "http"
  const effectiveSSLState: SSLState | "http" = isHttp
  ? "http"
  : state ?? "no_data"

  const sslLabels: Record<SSLState, string> = {
  critical: "🔥 Критично",
  warning: "⚠️ Попередження",
  invalid: "❌ Недійсний",
  no_data: "Немає даних",
  ok: "✅ Нормально",
};

const sslLabel = useMemo(() => {
  if (effectiveSSLState === "http") return "Без SSL (HTTP)"
  return sslLabels[effectiveSSLState as SSLState] ?? "—"
}, [effectiveSSLState])

const statusLabels: Record<SiteStatus, string> = {
  UP: "Працює",
  DOWN: "Недоступний",
  TIMEOUT: "Таймаут",
  ERROR: "Помилка",
}

  useEffect(() => {
    if (!expanded) return;

    setLoading(true);

    api.get(`/dashboard/site/${site_id}`, {
      params: { range }
    })
      .then(res => setRawData(res.data ?? []))
      .finally(() => setLoading(false));

  }, [expanded, site_id, range]);

const chartData = useMemo(() => {
  if (!rawData.length) return []

  return rawData
  .filter(c => c.bucket)
  .map(c => ({
    time: new Date(c.bucket!).getTime(),
    response_time: c.avg_response_time_ms ?? null,
    status: c.status,
    ssl_state: c.ssl_state,
    ssl_days_left: c.ssl_days_left,
    ssl_severity: c.ssl_severity,
    health: c.health,
  }))
}, [rawData])

  const threshold = 500;

  const updateInterval = async () => {
      try {
  await api.patch(`/sites/${site_id}/interval`, {
    check_interval: intervalEdit,
  });
} catch {
  alert("Не вдалося оновити інтервал");
}
};

  const average = useMemo(() => {
    const valid = chartData.filter(v => v.response_time != null)
    if (!valid.length) return 0
    return valid.reduce((acc, v) => acc + v.response_time!, 0) / valid.length
  }, [chartData])

  const handleArchive = async () => {
    if (!confirm("Архівувати сайт?")) return;
    await api.post(`/sites/${site_id}/deactivate`);
    onDeleted?.();
  };

  const handleReactivate = async () => {
    await api.post(`/sites/${site_id}/reactivate`);
    onReactivated?.();
  };

const handleExport = async () => {
  try {
    const response = await api.get(`/export/site/${site_id}`, {
      params: { range },
      responseType: "blob",
    });

    const blob = new Blob([response.data], { type: "text/csv" });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);

    link.href = url;
    link.setAttribute("download", `${name}_${range}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  } catch (e: any) {
  console.error(e)

  if (e?.response?.status === 500) {
    alert("Помилка сервера під час експорту")
  } else {
    alert("Експорт не вдався")
  }
}}

  return (
    <div
className={`rounded-xl p-6 shadow border-2 transition ${
archived
    ? "border-gray-400 opacity-70"
    : health === "critical"
    ? "border-red-600 bg-red-50"
    : health === "warning"
    ? "border-yellow-400 bg-yellow-50"
    : "border-gray-300"
}`}
>
  <div className="flex items-center gap-2">

  <StatusBadge status={last_status} />

<span className="text-xs font-semibold">
  {health === "critical" && "🔴 CRITICAL"}
  {health === "warning" && "🟡 WARNING"}
  {health === "healthy" && "🟢 HEALTHY"}
</span>
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
            · Остання перевірка: {last_checked_at
            ? new Date(last_checked_at).toLocaleString([], {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            })
            : "—"}
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
            onClick={handleExport}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200">
            Експорт CSV
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
              Архів
            </button>
          )}
        </div>
      </div>
<div className="grid grid-cols-3 gap-6 text-sm mt-4">
  <SLA label="24г" value={uptime_24h} />
  <SLA label="7д" value={uptime_7d} />
  <SLA label="30д" value={uptime_30d} />
</div>

<div className="grid grid-cols-2 gap-6 text-sm mt-4">
  <div>
    <div className="text-gray-500">p95 latency</div>
    <div className="font-semibold">
      {p95_latency != null ? `${Math.round(p95_latency)} ms` : "—"}
    </div>
  </div>

<div>
  <div className="text-gray-500">Error rate</div>

  {error_rate != null ? (
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

  <div className="text-xs text-gray-500">
  Стан = HTTP + SSL + помилки
</div>

<div className="flex gap-2 mt-4 text-sm">
  {["24h", "7d", "30d"].map(r => (
    <button
      key={r}
      onClick={() => setRange(r as any)}
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
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
            dataKey="time"
            tickFormatter={(v) => {
            const d = new Date(v)
            return range === "24h"
            ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : d.toLocaleDateString([], { day: '2-digit', month: '2-digit' })
            }}
            />
            <YAxis domain={[0, 'dataMax + 100']} />

            <Tooltip
  content={({ active, payload }) => {
    if (!active || !payload?.length) return null;

    const p = payload?.[0]?.payload;
    if (!p) return null;
    const sev = p.ssl_severity ?? null;
    const pointState = p.ssl_state ?? "no_data"
    const isHttpPoint = pointState === "http"

    const pointLabel = isHttpPoint
    ? "Без SSL (HTTP)"
    : sslLabels[pointState as SSLState] ?? "—"

    return (
      <div className="bg-white p-2 border rounded shadow text-xs">
        <div>{new Date(p.time).toLocaleString()}</div>

        <div>⏱ {p.response_time ?? "—"} ms</div>

        <div>
          Status: {p.status ? (statusLabels[p.status as SiteStatus] ?? "—") : "—"}
        </div>

        <div>
          🔐 SSL: {pointLabel}
        </div>

        <div>
        Health:
        {p.health === "critical" && " 🔴 Критично"}
        {p.health === "warning" && " 🟡 Попередження"}
        {p.health === "healthy" && " 🟢 Нормально"}
        </div>

        {p.ssl_days_left != null && (
          <div>
            {p.ssl_days_left <= 0
              ? "Термін дії закінчився"
              : `Закінчується через: ${p.ssl_days_left} днів`}
          </div>
        )}
    </div>
    );
  }}
/>

            <ReferenceLine y={average} stroke="orange" strokeDasharray="4 4" />
            <ReferenceLine y={threshold} stroke="red" strokeDasharray="2 2" />

            <Line
              dataKey="response_time"
  stroke="#2563eb"
dot={(props) => {
  const { payload } = props
  if (!payload) return false

  const colorMap = {
    critical: "#dc2626",
    warning: "#f59e0b",
    healthy: "#16a34a"
  }

  return <circle r={3} fill={colorMap[payload.health] || "#9ca3af"} />
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
function SLA({ label, value }: { label: string; value: number }) {
  let color = "text-gray-700";
  if (value === undefined || value === null) {
  return (
    <div>
      <div className="text-gray-500">SLA ({label})</div>
      <div className="text-gray-400">—</div>
    </div>
  )
}
  if (value < 90) color = "text-red-600";
  else if (value < 97) color = "text-yellow-600";
  else color = "text-green-600";

  return (
    <div>
      <div className="text-gray-500">SLA ({label})</div>
      <div className={`font-semibold ${color}`}>
        {value != null ? value.toFixed(2) : "—"}%
      </div>
    </div>
  );
}



