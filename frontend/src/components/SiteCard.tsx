import type { SiteStatus, SSLState } from "../types/api";
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
  ReferenceDot,
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
  last_checked_at: string;
  archived?: boolean;
  ssl_state?: SSLState | null;
  ssl_days_left?: number | null;
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
}: Props) {

  const [expanded, setExpanded] = useState(false);
  const [rawData, setRawData] = useState<Check[]>([]);
  const [loading, setLoading] = useState(false);
  const [range, setRange] = useState<"24h" | "7d" | "30d">("24h");
  const [intervalEdit, setIntervalEdit] = useState(check_interval);
  const isCritical = ssl_state === "critical";
const isBad =
  (last_status ? isProblem(last_status) : false) ||
  ssl_state === "invalid";

  const sslLabels: Record<SSLState, string> = {
  critical: "Критично",
  warning: "Попередження",
  invalid: "Недійсний",
  unknown: "Невідомо",
  no_data: "Немає даних",
  ok: "Нормально",
};

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
  return [...rawData]
    .sort(
      (a, b) =>
        new Date(a.checked_at).getTime() -
        new Date(b.checked_at).getTime()
    )
    .map(c => ({
      time: new Date(c.checked_at).toLocaleString(),
      response_time: c.response_time_ms ?? 0,
      status: c.status,
      ssl_state: c.ssl_state ?? "no_data",
      ssl_days_left: c.ssl_days_left,
    }));
}, [rawData]);

  const average =
    chartData.length > 0
      ? chartData.reduce((acc, v) => acc + v.response_time, 0) /
        chartData.length
      : 0;

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
};

  return (
    <div
      className={`rounded-xl p-5 shadow border-2 transition ${
  archived
    ? "bg-gray-50 border-gray-400 opacity-80"
    : isBad
  ? "bg-red-50 border-red-600"
    : isCritical
  ? "bg-orange-50 border-orange-500"
  : ssl_state === "warning"
  ? "bg-yellow-50 border-yellow-400"
  : "bg-white border-gray-500"
}`}
    >
  <div className="flex items-center gap-2">

  <StatusBadge status={last_status} />

{ssl_state === "ok" && (
    <span
    title={`SSL expires in ${ssl_days_left} days`}
    className="text-green-600 text-xs"
    >
    🔒 SSL
    </span>
     )}

  {ssl_state === "critical" && (
  <span
    title={`SSL expires in ${ssl_days_left} days`}
    className="text-red-600 text-xs font-semibold"
  >
    🔥 SSL
  </span>
)}

  {ssl_state === "warning" && (

    <span
    title={`SSL expires in ${ssl_days_left} days`}
    className="text-yellow-600 text-xs">
      ⚠️ SSL
    </span>
  )}

  {ssl_state === "invalid" && (
    <span
    title="SSL certificate invalid or expired"
    className="text-red-700 text-xs font-semibold">

      ❌ SSL
    </span>
  )}

{(ssl_state === "unknown" || ssl_state === "no_data") && (
  <span className="text-gray-400 text-xs">⭕ SSL</span>
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
            · Остання перевірка: {last_checked_at
  ? new Date(last_checked_at).toLocaleString()
  : "—"}
          </div>
        </div>

          <button
            onClick={() => setExpanded(!expanded)}
            className="px-3 py-1 bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100"
          >
            {expanded ? "Приховати" : "Деталі"}
          </button>
            <button
            onClick={handleExport}
            className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
            Експорт у CSV
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

      <div className="grid grid-cols-3 gap-4 text-sm mt-4">
  <SLA label="24г" value={uptime_24h} />
  <SLA label="7д" value={uptime_7d} />
  <SLA label="30д" value={uptime_30d} />
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

{expanded && (
  <>
    <div className="text-xs text-gray-500 mb-2 flex gap-3">
      <span>🔴 Down</span>
      <span>🔥 SSL critical</span>
      <span>⚠️ SSL warning</span>
    </div>

    <div className="mt-6 h-72">
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
            <XAxis dataKey="time" hide />
            <YAxis />

            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;

                const p = payload[0].payload;

                return (
                  <div className="bg-white p-2 border rounded shadow text-xs">
                    <div>⏱ {p.response_time} ms</div>

                    <div>
                        🔐 SSL: {sslLabels[p.ssl_state as SSLState] ?? p.ssl_state ?? "—"}
                    </div>

                    {p.ssl_days_left != null && (
                    <div>
                    {p.ssl_days_left <= 0
                    ? "Expired"
                    : `Expires in: ${p.ssl_days_left} days`}
                    </div>
                    )}


                  </div>
                );
              }}
            />

            <ReferenceLine y={average} stroke="orange" strokeDasharray="4 4" />
            <ReferenceLine y={threshold} stroke="red" strokeDasharray="2 2" />

            <Line
              type="monotone"
              dataKey="response_time"
              stroke="#2563eb"
              strokeWidth={2}
              dot={false}
            />

            {chartData.map((point, i) => {
              if (point.ssl_state === "critical") {
                return (
                  <ReferenceDot
                    key={`critical-${i}`}
                    x={point.time}
                    y={point.response_time}
                    r={4}
                    fill="red"
                  />
                );
              }

              if (point.ssl_state === "warning") {
                return (
                  <ReferenceDot
                    key={`warning-${i}`}
                    x={point.time}
                    y={point.response_time}
                    r={4}
                    fill="orange"
                  />
                );
              }
                if (point.ssl_state === "invalid") {
                    return (
                  <ReferenceDot
                    key={`invalid-${i}`}
                    x={point.time}
                    y={point.response_time}
                    r={4}
                    fill="darkred"
                  />
                );
              }

                if (point.ssl_state === "unknown") {
                return (
                <ReferenceDot
                key={`unknown-${i}`}
                x={point.time}
                y={point.response_time}
                r={4}
                fill="lightgray"
                />
                );
                }

                if (point.ssl_state === "no_data") {
                    return (
                  <ReferenceDot
                    key={`no_data-${i}`}
                    x={point.time}
                    y={point.response_time}
                    r={4}
                    fill="gray"
                  />
                );
              }


              return null;
            })}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  </>
)}
    </div>
  );
}
function SLA({ label, value }: { label: string; value: number }) {
  let color = "text-gray-700";
  if (value < 90) color = "text-red-600";
  else if (value < 97) color = "text-yellow-600";
  else color = "text-green-600";

  return (
    <div className="border rounded-lg p-3 text-center bg-gray-50">
      <div className="text-xs text-gray-500">{label}</div>
      <div className={`font-semibold ${color}`}>
        {value?.toFixed(2)}%
      </div>
    </div>
  );
}