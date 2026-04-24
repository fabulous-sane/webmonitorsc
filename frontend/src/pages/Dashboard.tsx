import { useEffect, useState } from "react";
import api from "../api/axios";
import SiteCard from "../components/SiteCard";
import Header from "../components/Header";
import TelegramConnect from "../components/TelegramConnect";
import AddSiteModal from "../components/AddSiteModal";
import SystemSummary from "../components/SystemSummary";
import RetentionPanel from "../components/RetentionPanel";
import { isProblem } from "../types/status";
import type { DashboardItem, SiteStatus } from "../types/api";
import type { SystemStatus } from "../components/SystemSummary";
import { normalizeSSL, sslMeta } from "../utils/ssl"

type HealthFilter = "ALL" | "HEALTHY" | "WARNING" | "CRITICAL";
type StatusFilter = "ВСІ" | "UP" | "DOWN" | "ERROR" | "TIMEOUT";
type ActivityFilter = "ВСІ" | "АКТИВНІ" | "АРХІВОВАНІ";
type SSLFilter =
  | "ALL"
  | "OK"
  | "WARNING"
  | "CRITICAL"
  | "INVALID"
  | "NO_DATA"
  | "NO_SSL";

export default function Dashboard() {
  const [sites, setSites] = useState<DashboardItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [healthFilter, setHealthFilter] = useState<HealthFilter>("ALL");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ВСІ");
  const [activityFilter, setActivityFilter] = useState<ActivityFilter>("ВСІ");
  const [sslFilter, setSslFilter] = useState<SSLFilter>("ALL");

  const sslButtons = [
  { key: "ALL", label: "ВСІ" },
  { key: "OK", label: "OK" },
  { key: "WARNING", label: "⚠" },
  { key: "CRITICAL", label: "🔥" },
  { key: "INVALID", label: "❌" },
  { key: "NO_DATA", label: "Немає даних" },
  { key: "NO_SSL", label: "Без SSL" },
];

  const loadSites = async () => {
    try {
      const res = await api.get("/dashboard/overview");
      setSites(res.data as DashboardItem[]);
    } catch {
      setSites([]);
    }
  };

  useEffect(() => {
    loadSites().finally(() => setLoading(false));

    const interval = setInterval(loadSites, 30000);
    return () => clearInterval(interval);
  }, []);

const [systemData, setSystemData] = useState<SystemStatus | null>(null)
    useEffect(() => {
  api.get("/system/status")
    .then(res => setSystemData(res.data))
}, [])

if (loading) return <div className="p-10">Завантаження...</div>;

const filteredSites = sites.filter(s => {
  const state = normalizeSSL(s.ssl_state)

  // activity
  if (activityFilter === "АКТИВНІ" && !s.is_active) return false
  if (activityFilter === "АРХІВОВАНІ" && s.is_active) return false

  // http status
  if (statusFilter === "DOWN" && !isProblem(s.last_status)) return false
  if (
    statusFilter !== "ВСІ" &&
    statusFilter !== "DOWN" &&
    s.last_status !== statusFilter
  )
    return false

  // health
  if (healthFilter === "CRITICAL" && s.health !== "critical") return false
  if (healthFilter === "WARNING" && s.health !== "warning") return false
  if (healthFilter === "HEALTHY" && s.health !== "healthy") return false

  // ssl
  if (sslFilter === "CRITICAL" && state !== "critical") return false
  if (sslFilter === "WARNING" && state !== "warning") return false
  if (sslFilter === "INVALID" && state !== "invalid") return false
  if (sslFilter === "OK" && state !== "ok") return false
  if (sslFilter === "NO_DATA" && state !== "no_data") return false
  if (sslFilter === "NO_SSL" && state !== "http") return false

  return true
})

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <div className="flex-1 max-w-6xl mx-auto w-full px-8 py-6 flex flex-col space-y-6">

        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-semibold">Дашборд</h2>

          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg shadow"
          >
            + Додати сайт
          </button>
        </div>
    <div className="space-y-6">

<SystemSummary data={systemData} />
{systemData && <RetentionPanel data={systemData} />}

  {/* FILTERS */}
  <div className="space-y-4">

  {/* Activity */}
    <div className="flex gap-2">
      {["ВСІ", "АКТИВНІ", "АРХІВОВАНІ"].map(f => (
        <button
          key={f}
          onClick={() => setActivityFilter(f as ActivityFilter)}
          className={`px-4 py-1 rounded-md ${
            activityFilter === f
              ? "bg-blue-600 text-white"
              : "bg-gray-200"
          }`}
        >
          {f}
        </button>
      ))}
    </div>

{/* Health */}
    <div>
      <div className="text-xs text-gray-400 mb-1">
        Загальний стан (HTTP + SSL + помилки)
      </div>
      <div className="flex gap-2">
        {[
  { key: "ALL", label: "ВСІ" },
  { key: "HEALTHY", label: "Нормально" },
  { key: "WARNING", label: "Попередження" },
  { key: "CRITICAL", label: "Критично" },
].map(f => (
          <button
            key={f.key}
            onClick={() => setHealthFilter(f.key as HealthFilter)}
            className={`px-3 py-1 rounded-md ${
              healthFilter === f.key
                ? "bg-green-600 text-white"
                : "bg-gray-200"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>
    </div>

  {/* SSL */}
    <div>
      <div className="text-xs text-gray-400 mb-1">SSL</div>
      <div className="flex gap-2 flex-wrap">
        {sslButtons.map(b => (
            <button
            key={b.key}
            onClick={() => setSslFilter(b.key as SSLFilter)}
            className={`px-3 py-1 rounded-md ${
              sslFilter === b.key
                ? "bg-purple-600 text-white"
                : "bg-gray-200"
            }`}
          >
            {b.label}
  </button>
))}
      </div>
    </div>

  {/* HTTP */}
    <div>
      <div className="text-xs text-gray-400 mb-1">HTTP</div>
      <div className="flex gap-2">
        {["ВСІ", "UP", "DOWN", "ERROR", "TIMEOUT"].map(s => (
          <button
            key={s}
            onClick={() => setStatusFilter(s as StatusFilter)}
            className={`px-3 py-1 rounded-md ${
              statusFilter === s
                ? "bg-black text-white"
                : "bg-gray-200"
            }`}
          >
            {s}
          </button>
        ))}
      </div>
    </div>

  </div>

{/* CONTENT */}
<div className="flex gap-6 items-start">

    <div className="flex-1 min-w-0 space-y-4">
      {filteredSites.length === 0 ? (
        <div className="text-gray-400 text-sm">
          Немає сайтів
        </div>
      ) : (
        filteredSites.map(site => (
          <SiteCard
            key={site.site_id}
            {...site}
            archived={!site.is_active}
            onDeleted={loadSites}
            onReactivated={loadSites}
          />
        ))
      )}
    </div>

          <div className="w-80 shrink-0">
            <TelegramConnect />
          </div>

        </div>
    </div>
        </div>
      {showModal && (
        <AddSiteModal
          onClose={() => setShowModal(false)}
          onCreated={loadSites}
        />
      )}

    </div>
  );
}

