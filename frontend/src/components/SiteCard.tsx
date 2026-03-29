import { useState, useEffect, useMemo } from "react";
import api from "../api/axios";
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
  last_status: "UP" | "DOWN" | null;
  uptime_24h: number;
  uptime_7d: number;
  uptime_30d: number;
  check_interval: number;
  last_checked_at: string;
  archived?: boolean;
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
}: Props) {

  const [expanded, setExpanded] = useState(false);
  const [rawData, setRawData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [range, setRange] = useState<"24h" | "7d" | "30d">("24h");

  const [intervalEdit, setIntervalEdit] = useState(check_interval);

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
      }));
  }, [rawData]);

  const average =
    chartData.length > 0
      ? chartData.reduce((acc, v) => acc + v.response_time, 0) /
        chartData.length
      : 0;

  const threshold = 500;

  const updateInterval = async () => {
    await api.patch(`/sites/${site_id}/interval`, {
      check_interval: intervalEdit,
    });
    onDeleted?.();
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
  link.href = window.URL.createObjectURL(blob);
  link.download = `${name}_${range}.csv`;
  link.click();
};

  return (
    <div
      className={`rounded-xl p-5 shadow border-2 transition ${
        archived
          ? "bg-gray-50 border-gray-400 opacity-80"
          : last_status === "DOWN"
          ? "bg-red-50 border-red-500"
          : "bg-white border-gray-500"
      }`}
    >
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
            · Остання перевірка: {new Date(last_checked_at).toLocaleString()}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {last_status && (
            <span
              className={`px-3 py-1 rounded-full text-sm ${
                last_status === "UP"
                  ? "bg-green-100 text-green-700"
                  : "bg-red-100 text-red-700"
              }`}
            >
              {last_status}
            </span>
          )}

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
      </div>

      {/* SLA */}
      <div className="grid grid-cols-3 gap-4 text-sm mt-4">
        <SLA label="24г" value={uptime_24h} />
        <SLA label="7д" value={uptime_7d} />
        <SLA label="30д" value={uptime_30d} />
      </div>
       {/* RANGE SWITCHER */}
<div className="flex gap-2 mt-4 text-sm">
  {["24h", "7d", "30d"].map(r => (
    <button
      key={r}
      onClick={() => setRange(r as any)}
      className={`px-3 py-1 rounded-md transition ${
        range === r
          ? "bg-blue-600 text-white"
          : "bg-gray-200 hover:bg-gray-300"
      }`}
    >
      {r}
    </button>
  ))}
</div>
      {/* CHART */}
      {expanded && (
        <div className="mt-6 h-72">
          {loading || chartData.length === 0 ? (
            <div className="text-center text-gray-500 mt-20">
              Немає даних
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" hide />
                <YAxis />
                <Tooltip />

                <ReferenceLine
                  y={average}
                  stroke="orange"
                  strokeDasharray="4 4"
                />

                <ReferenceLine
                  y={threshold}
                  stroke="red"
                  strokeDasharray="2 2"
                />

                <Line
                  type="monotone"
                  dataKey="response_time"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                />

                {chartData.map((point, i) =>
                  point.status === "DOWN" ? (
                    <ReferenceDot
                      key={i}
                      x={point.time}
                      y={point.response_time}
                      r={5}
                      fill="red"
                    />
                  ) : null
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
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