import { useEffect, useState } from "react";
import api from "../api/axios";

interface SystemStatus {
  active_sites: number;
  archived_sites: number;
  checks_24h: number;
  retention_next_run: string | null;
}

export default function SystemSummary({
  onFilterChange,
}: {
  onFilterChange?: (filter: "ALL" | "ACTIVE" | "ARCHIVED") => void;
}) {
  const [data, setData] = useState<SystemStatus | null>(null);

  useEffect(() => {
    api.get("/system/status")
      .then(res => setData(res.data))
      .catch(err => console.error(err));
  }, []);

  if (!data) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-sm border">
        Завантаження системних даних...
      </div>
    );
  }

  const retentionTime = data.retention_next_run
    ? new Date(data.retention_next_run).toLocaleString()
    : "—";

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4">

      <div className="text-lg font-semibold">
        Огляд системи
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

        <SummaryCard
          label="Активні сайти"
          value={data.active_sites}
          onClick={() => onFilterChange?.("ACTIVE")}
        />

        <SummaryCard
          label="Архівовані"
          value={data.archived_sites}
          onClick={() => onFilterChange?.("ARCHIVED")}
        />

        <SummaryCard
          label="Перевірок (24г)"
          value={data.checks_24h}
        />

        <SummaryCard
          label="Наступна очистка"
          value={retentionTime}
        />

      </div>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  onClick,
}: {
  label: string;
  value: number | string;
  onClick?: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg border cursor-pointer transition hover:shadow-md ${
        onClick ? "hover:bg-gray-50" : ""
      }`}
    >
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}