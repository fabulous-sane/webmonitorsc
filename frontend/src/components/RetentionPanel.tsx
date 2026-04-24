import { useState } from "react"
import type { SystemStatus } from "../components/SystemSummary"
export default function RetentionPanel({ data }: { data: SystemStatus }) {
  const [open, setOpen] = useState(false)

const formatKyiv = (d?: string | null) =>
  d
    ? new Date(d).toLocaleString("uk-UA", {
        timeZone: "Europe/Kyiv",
      })
    : "—"

  return (
    <div className="bg-white rounded-xl shadow-sm border">

     <button
  onClick={() => setOpen(!open)}
  className="w-full flex justify-between items-center p-4"
>
  <span className="text-sm font-medium text-gray-600">
    Система зберігання даних
  </span>

  <span className="text-xs text-gray-400">
    {open ? "Згорнути" : "Розгорнути"}
  </span>
</button>

      {open && (
  <div className="p-4 space-y-3 text-sm text-gray-600">

  <div className="font-medium">
    {data.retention_broken
      ? "❌ Планувальник не працює"
      : data.retention_never_run
      ? "⏳ Ще не запускалось"
      : data.retention_delayed
      ? "⚠ Є затримка"
      : "✅ Працює стабільно"}
  </div>

    <div className="space-y-1 text-xs text-gray-500">
    <div>
      Зберігаємо дані за останні <b>{data.data_retention_days} днів</b>
    </div>

     <div>
      Видаляються записи старші ніж:
      <br />
      <b>
        {formatKyiv(data.data_cutoff_date)}
      </b>
    </div>

    <div>
      Останнє очищення:
      <b> {formatKyiv(data.retention_last_run)}</b>
    </div>

    <div>
      Видалено записів:
      <b> {data.retention_deleted_last ?? 0}</b>
    </div>

    <div>
      Наступний запуск:
      <b> {formatKyiv(data.retention_next_run)}</b>
    </div>
    </div>
  </div>
)}
    </div>
  )
}