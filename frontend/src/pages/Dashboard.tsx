import { useEffect, useState } from "react";
import api from "../api/axios";
import SiteCard from "../components/SiteCard";
import Header from "../components/Header";
import TelegramConnect from "../components/TelegramConnect";
import AddSiteModal from "../components/AddSiteModal";
import SystemSummary from "../components/SystemSummary";

interface DashboardItem {
  site_id: string;
  name: string;
  url: string;
  last_status: "UP" | "DOWN" | null;
  uptime_24h: number;
  uptime_7d: number;
  uptime_30d: number;
  check_interval: number;
  last_checked_at: string;
  is_active: boolean;
}

export default function Dashboard() {
  const [sites, setSites] = useState<DashboardItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [statusFilter, setStatusFilter] =
    useState<"ВСІ" | "UP" | "DOWN">("ВСІ");

  const [activityFilter, setActivityFilter] =
    useState<"ВСІ" | "АКТИВНІ" | "АРХІВОВАНІ">("ВСІ");

  const loadSites = async () => {
    const res = await api.get("/dashboard/overview");
    setSites(res.data);
  };

  useEffect(() => {
    loadSites().finally(() => setLoading(false));

    const interval = setInterval(() => {
      if (document.visibilityState === "visible") {
        loadSites();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="p-10">Завантаження...</div>;

  const total = sites.length;
  const active = sites.filter(s => s.is_active).length;
  const archived = sites.filter(s => !s.is_active).length;

  let filteredSites = sites;

  if (activityFilter === "АКТИВНІ") {
    filteredSites = filteredSites.filter(s => s.is_active);
  }

  if (activityFilter === "АРХІВОВАНІ") {
    filteredSites = filteredSites.filter(s => !s.is_active);
  }

  if (statusFilter !== "ВСІ") {
    filteredSites = filteredSites.filter(
      s => s.last_status === statusFilter
    );
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      <Header />

      <div className="flex-1 max-w-6xl mx-auto w-full px-8 py-6 flex flex-col space-y-6">

        {/* HEADER ACTION */}
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-semibold">Дашборд</h2>

          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg shadow transition"
          >
            + Додати сайт
          </button>
        </div>

        {/* SUMMARY */}
        <SystemSummary
          activeSites={active}
          archivedSites={archived}
          totalSites={total}
        />

        {/* FILTERS */}
        <div className="flex gap-4 text-sm">

          {["ВСІ", "АКТИВНІ", "АРХІВОВАНІ"].map(f => (
            <button
              key={f}
              onClick={() => setActivityFilter(f as any)}
              className={`px-4 py-1 rounded-md transition ${
                activityFilter === f
                  ? "bg-blue-600 text-white shadow"
                  : "bg-gray-200 hover:bg-gray-300"
              }`}
            >
              {f.charAt(0) + f.slice(1).toLowerCase()}
            </button>
          ))}

          <div className="ml-8 flex gap-4 items-center">
            <span className="text-gray-600">Статус:</span>

            {["ВСІ", "UP", "DOWN"].map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s as any)}
                className={`px-3 py-1 rounded-md transition ${
                  statusFilter === s
                    ? s === "DOWN"
                      ? "bg-red-600 text-white"
                      : s === "UP"
                      ? "bg-green-600 text-white"
                      : "bg-gray-800 text-white"
                    : "bg-gray-200 hover:bg-gray-300"
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* SITES */}
        <div className="flex gap-6 flex-1">
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">

            {filteredSites.length === 0 && (
              <div className="text-gray-400 text-sm">
                Немає сайтів за даним фільтром.
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