import { useState } from "react"
import type { SystemStatus } from "../components/SystemSummary"
export default function RetentionPanel({ data }: { data: SystemStatus }) {
  const [open, setOpen] = useState(false)

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
  <div className="space-y-2 text-xs text-gray-500">

    <div className="p-4 border-b">
      {data.retention_broken
        ? "❌ Зламано"
        : data.retention_never_run
        ? "⏳ Не запускалась"
        : data.retention_delayed
        ? "⚠ Затримка"
        : "✅ Працює нормально"}
    </div>

    <div>
      Зберігаємо історію за останні: {data.data_retention_days} днів
    </div>

          <div>
      Дані старші за цю дату будуть видалені:
      <br />
      {data.data_cutoff_date
        ? new Date(data.data_cutoff_date).toLocaleString("uk-UA", {
            timeZone: "Europe/Kyiv",
          })
        : "—"}
    </div>

          <div>
      Останнє очищення:
      {data.retention_last_run
        ? new Date(data.retention_last_run).toLocaleString("uk-UA", {
            timeZone: "Europe/Kyiv",
          })
        : " —"}
    </div>

          <div>
      Видалено записів: {data.retention_deleted_last ?? 0}
    </div>

    <div>
      Наступне очищення:
      {data.retention_next_run
        ? new Date(data.retention_next_run).toLocaleString("uk-UA", {
            timeZone: "Europe/Kyiv",
          })
        : " —"}
    </div>
  </div>
)}
    </div>
  )
}