import { useEffect, useState } from "react";
import api from "../api/axios";
import SiteCard from "../components/SiteCard";
import Header from "../components/Header";
import TelegramConnect from "../components/TelegramConnect";
import AddSiteModal from "../components/AddSiteModal";
import SystemSummary from "../components/SystemSummary";
import { isProblem } from "../types/status";
import type { DashboardItem, SiteStatus } from "../types/api";

type StatusFilter = "ВСІ" | "UP" | "DOWN" | "ERROR" | "TIMEOUT";
type ActivityFilter = "ВСІ" | "АКТИВНІ" | "АРХІВОВАНІ";
type SSLFilter =
  | "ALL"
  | "OK"
  | "WARNING"
  | "CRITICAL"
  | "INVALID"
  | "UNKNOWN";


export default function Dashboard() {
  const [sites, setSites] = useState<DashboardItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ВСІ");
  const [activityFilter, setActivityFilter] = useState<ActivityFilter>("ВСІ");
  const [sslFilter, setSslFilter] = useState<SSLFilter>("ALL");

  const sslButtons = [
  { key: "ALL", label: "ALL" },
  { key: "OK", label: "OK" },
  { key: "WARNING", label: "⚠" },
  { key: "CRITICAL", label: "🔥" },
  { key: "INVALID", label: "❌" },
  { key: "UNKNOWN", label: "?" },
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

  if (loading) return <div className="p-10">Завантаження...</div>;

  let filteredSites = sites;

  if (activityFilter === "АКТИВНІ") {
    filteredSites = filteredSites.filter(s => s.is_active);
  }

  if (activityFilter === "АРХІВОВАНІ") {
    filteredSites = filteredSites.filter(s => !s.is_active);
  }

  if (statusFilter === "DOWN") {
    filteredSites = filteredSites.filter(s =>
      isProblem(s.last_status)
    );
  } else if (statusFilter !== "ВСІ") {
    filteredSites = filteredSites.filter(
      s => s.last_status === statusFilter
    );
  }

if (sslFilter !== "ALL") {
  filteredSites = filteredSites.filter(s => {
    const state = s.ssl_state ?? "no_data";
    if (sslFilter === "OK") return state === "ok";
    if (sslFilter === "WARNING") return state === "warning";
    if (sslFilter === "CRITICAL") return state === "critical";
    if (sslFilter === "INVALID") return state === "invalid";
    if (sslFilter === "UNKNOWN") {
    return state === "unknown" || state === "no_data";
    }

    return true;
  });
}

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
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

        <SystemSummary />

        <div className="flex gap-4 text-sm">
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

            <div className="ml-8 flex gap-2">
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

          <div className="ml-8 flex gap-4">
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

        <div className="flex gap-6 flex-1">
          <div className="flex-1 overflow-y-auto space-y-4">

            {filteredSites.length === 0 && (
              <div className="text-gray-400 text-sm">
                Немає сайтів
              </div>
            )}

            {filteredSites.map(site => (
              <SiteCard
                key={site.site_id}
                {...site}
                archived={!site.is_active}
                onDeleted={loadSites}
                onReactivated={loadSites}
              />
            ))}
          </div>

          <div className="w-80">
            <TelegramConnect />
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