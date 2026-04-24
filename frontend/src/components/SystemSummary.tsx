import api from "../api/axios";

interface SystemStatus {
  active_sites: number;
  archived_sites: number;
  checks_24h: number;

  ssl_critical_sites: number;
  ssl_warning_sites: number;
  ssl_invalid_sites: number;
  ssl_no_data_sites: number;
  ssl_no_ssl_sites: number;
  ssl_ok_sites: number;

  problematic_sites: number;

  ssl_invalid_events: number;
  ssl_critical_events: number;
  ssl_warning_events: number;
  ssl_no_data_events: number;

  data_retention_days: number;
  data_cutoff_date: string;

  retention_next_run: string | null;
  retention_last_run: string | null;
  retention_deleted_last: number | null;

  retention_never_run: boolean;
  retention_broken: boolean;
  retention_delayed: boolean;
}

export default function SystemSummary({ data }: { data: SystemStatus | null }) {

  if (!data) {
    return (
      <div className="bg-white p-6 rounded-xl shadow-sm border">
        Завантаження...
      </div>
    );
  }

  return (
  <div className="bg-white p-6 rounded-xl shadow-sm border space-y-6">

      {/* HEADER */}
      <div className="text-lg font-semibold">
      Огляд системи
    </div>

    <div className="space-y-4">
      {/* GLOBAL */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
        <Card label="Активні сайти" value={data.active_sites} />
        <Card label="Архівовані" value={data.archived_sites} />
        <Card label="Перевірки (сьогодні)" value={data.checks_24h} />
    </div>

      {/* SSL SITES */}
      <div>
        <div className="text-sm font-medium text-gray-500 mb-2">
          SSL стан (сайти)
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          <Card
            label="Critical"
            value={data.ssl_critical_sites}
            className="bg-red-50 text-red-600"
          />

          <Card
            label="Warning"
            value={data.ssl_warning_sites}
            className="bg-yellow-50 text-yellow-600"
          />

          <Card
            label="Invalid"
            value={data.ssl_invalid_sites}
            className="bg-red-100 text-red-700"
          />

          <Card
            label="OK"
            value={data.ssl_ok_sites}
            className="bg-green-50 text-green-700"
          />

           <Card
            label="Без SSL"
            value={data.ssl_no_ssl_sites ?? 0}
            className="bg-gray-200"
            />
        </div>
      </div>

      {/* SSL EVENTS */}
      <div>
        <div className="text-sm font-medium text-gray-500 mb-2">
          SSL події (сьогодні)
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <Card
            label="Critical"
            value={data.ssl_critical_events}
            className="bg-red-100"
          />

          <Card
            label="Warning"
            value={data.ssl_warning_events}
            className="bg-yellow-100"
          />

          <Card
            label="Invalid"
            value={data.ssl_invalid_events}
            className="bg-red-100"
          />

          <Card
            label="No data"
            value={data.ssl_no_data_events}
            className="bg-gray-100"
          />
        </div>
      </div>
    </div>
   </div>
);}

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


