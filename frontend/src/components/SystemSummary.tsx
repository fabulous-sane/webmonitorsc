import { useEffect, useState } from "react";
import api from "../api/axios";

interface SystemStatus {
  active_sites: number;
  archived_sites: number;
  checks_24h: number;

  ssl_critical_sites: number;
  ssl_warning_sites: number;
  ssl_invalid_sites: number;
  ssl_unknown_sites: number;
  ssl_ok_sites: number;

  ssl_invalid_events: number;
  ssl_critical_events: number;
  ssl_warning_events: number;
  ssl_unknown_events: number;

  retention_next_run: string | null;
}

export default function SystemSummary() {
  const [data, setData] = useState<SystemStatus | null>(null);

  useEffect(() => {
    api.get("/system/status")
      .then(res => setData(res.data))
      .catch(console.error);
  }, []);

  if (!data) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-sm border">
        Завантаження...
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4">

      <div className="text-lg font-semibold">
        Огляд системи
      </div>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">

        <Card label="Активні" value={data.active_sites} />
        <Card label="Архів" value={data.archived_sites} />
        <Card label="Перевірки (події 24г)" value={data.checks_24h} />

        <Card
          label="SSL критично"
          value={data.ssl_critical_sites ?? 0}
          className="bg-red-50 text-red-600"
        />

        <Card
          label="SSL warning"
          value={data.ssl_warning_sites ?? 0}
          className="bg-yellow-50 text-yellow-600"
        />

        <Card
  label="SSL critical (24г)"
  value={data.ssl_critical_events ?? 0}
  className="bg-gray-50"
/>

<Card
  label="SSL warning (24г)"
  value={data.ssl_warning_events ?? 0}
  className="bg-yellow-50"
/>
<Card
  label="SSL invalid"
  value={data.ssl_invalid_sites ?? 0}
  className="bg-red-100 text-red-700"
/>
<Card
  label="SSL invalid (24г)"
  value={data.ssl_invalid_events ?? 0}
  className="bg-red-100"
/>
<Card
  label="SSL unknown"
  value={data.ssl_unknown_sites ?? 0}
  className="bg-gray-100"
/>
<Card
  label="SSL unknown (24г)"
  value={data.ssl_unknown_events ?? 0}
  className="bg-gray-100"
/>
<Card
  label="SSL OK"
  value={data.ssl_ok_sites ?? 0}
  className="bg-green-50 text-green-700"
/>

      </div>
    </div>
  );
}

function Card({
  label,
  value,
  className = ""
}: {
  label: string;
  value: number | string;
  className?: string;
}) {
  return (
    <div className={`p-4 rounded-lg border ${className}`}>
      <div className="text-sm text-gray-500">{label}</div>
      <div className="text-xl font-semibold">{value}</div>
    </div>
  );
}