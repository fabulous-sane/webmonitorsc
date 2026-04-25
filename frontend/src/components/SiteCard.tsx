import { sslMeta, sslLabels } from "../utils/ssl"
import type { SiteStatus, SSLState, SSLSeverity } from "../types/api";
import { useState, useEffect, useMemo } from "react";
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
  ssl_severity?: SSLSeverity;
  p95_latency?: number;
  error_rate?: number;
  health?: "healthy" | "warning" | "critical" | "no_data";
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

  const statusLabels: Record<SiteStatus, string> = {
  UP: "Працює",
  DOWN: "Недоступний",
  TIMEOUT: "Таймаут",
  ERROR: "Помилка",
}

const formatDate = (d: string | null) => {
  if (!d) return "—"
  const date = new Date(d)
  if (isNaN(date.getTime())) return "—"

  return date.toLocaleString("uk-UA", {
    timeZone: "Europe/Kyiv",
  })
}

const sslState = ssl_state ?? "no_data"
const sslLabel = sslLabels[sslState]

  useEffect(() => {
    if (!expanded) return;

    setLoading(true);

    api.get(`/dashboard/site/${site_id}`, {
      params: { range }
    })
      .then(res => setRawData(res.data ?? []))
      .catch(() => setRawData([]))
      .finally(() => setLoading(false));

  }, [expanded, site_id, range]);

const chartData = useMemo(() => {
  if (!rawData.length) return []

  return rawData
    .filter(c => c.checked_at)
    .map(c => {
      const rt = c.avg_response_time_ms ?? c.response_time_ms
      const t = new Date(c.checked_at!)
      const time = isNaN(t.getTime()) ? Date.now() : t.getTime()
      return {
        time: new Date(c.checked_at!).getTime(),
        response_time: Number.isFinite(rt) && rt! >= 0 ? rt : null,
        status: c.status,
        ssl_state: c.ssl_state ?? "no_data",
        ssl_days_left: c.ssl_days_left,
        ssl_severity: c.ssl_severity,
        health: c.health ?? "no_data",
      }
    })
}, [rawData])

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
  const valid = chartData.filter(v => v.response_time != null)
  if (!valid.length) return null

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
    ? "border-red-600"
    : health === "warning"
    ? "border-yellow-400"
    : "border-gray-300"
}`}
>
  <div className="flex items-center gap-2">
  <StatusBadge status={last_status} />

<span className="text-xs font-semibold">
  {health === "critical" && "🔴 Критично"}
  {health === "warning" && "🟡 Попередження"}
  {health === "healthy" && "🟢 Нормально"}
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
              Архівувати
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
        <ResponsiveContainer width="100%" height="100%">
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
           <YAxis domain={[0, (dataMax: number) => dataMax * 1.2]} />

            <Tooltip
    content={({ active, payload }) => {
    if (!active || !payload?.length) return null;

    const p = payload?.[0]?.payload;
    if (!p) return null;

const pointState = p.ssl_state ?? "no_data"
const isHttp = sslState === "http"
const pointMeta = sslMeta[pointState] ?? {
  label: "Невідомо",
  severity: "warn"
}

const healthLabels = {
  critical: "🔴 Критично",
  warning: "🟡 Попередження",
  healthy: "🟢 Нормально",
  no_data: "⚪ Немає даних",
}

const healthKey = p.health ?? "no_data"
    const pointLabel = pointMeta?.label ?? "—"

    return (
      <div className="bg-white p-2 border rounded shadow text-xs">
        <div>
        {new Date(p.time).toLocaleString("uk-UA", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  timeZone: "Europe/Kyiv"
})}
        </div>

        <div>⏱ {p.response_time != null ? `${p.response_time} ms` : "—"}</div>

        <div>
          Статус: {p.status ? (statusLabels[p.status as keyof typeof statusLabels] ?? "—") : "—"}
        </div>

        {!isHttp && (
  <div className="font-medium">
    {pointMeta.label}
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

const colorMap = {
      critical: "#dc2626",
      warning: "#f59e0b",
      healthy: "#16a34a",
      no_data: "#9ca3af"
    }

    const healthKey = payload.health ?? "no_data"
return (
      <circle
        r={3}
        fill={colorMap[healthKey] ?? "#9ca3af"}
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

function SLA({ label, value }: { label: string; value: number }) {
  let color = "text-gray-700";
  if (!Number.isFinite(value)) {
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
        {Number.isFinite(value) ? value.toFixed(2) : "—"}%
      </div>
    </div>
  );
}



