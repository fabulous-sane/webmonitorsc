import type { SiteStatus } from "../types/api";

interface Props {
  status: SiteStatus | null;
}

export default function StatusBadge({ status }: Props) {
  const map: Record<SiteStatus, string> = {
    UP: "bg-green-100 text-green-700",
    DOWN: "bg-red-100 text-red-700",
    TIMEOUT: "bg-yellow-100 text-yellow-700",
    ERROR: "bg-orange-100 text-orange-700",
  };

  const label: Record<SiteStatus, string> = {
    UP: "Працює",
    DOWN: "Недоступний",
    TIMEOUT: "Таймаут",
    ERROR: "Помилка",
  };

if (!status) {
  return <span className="text-gray-400 text-xs">—</span>;
}

const cls = map[status] ?? "bg-gray-100 text-gray-500"
const text = label[status] ?? "Unknown"

return (
  <span className={`px-3 py-1 text-xs rounded-full ${cls}`}>
  {text}
    </span>
);

}