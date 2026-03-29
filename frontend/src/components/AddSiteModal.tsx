import { useState } from "react";
import api from "../api/axios";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function AddSiteModal({ onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [interval, setInterval] = useState(60);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleCreate = async () => {
    if (!name || !url) {
      setError("Всі поля мають бути заповнені!");
      return;
    }

    if (interval < 30) {
      setError("Мінімальний інтервал - 30 секунд");
      return;
    }

    try {
      setLoading(true);

      await api.post("/sites", {
        name,
        url,
        check_interval: interval,
      });

      onCreated();
      onClose();
    } catch {
      setError("Не вдалося створити перевірку.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center">
      <div className="bg-white p-6 rounded-xl w-[420px] space-y-4 shadow-lg">
        <h3 className="text-lg font-semibold">Додати сайт</h3>

        {error && (
          <div className="bg-red-50 text-red-600 p-2 rounded text-sm">
            {error}
          </div>
        )}

        <input
          placeholder="Назва сайту"
          className="w-full border p-2 rounded"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <input
          placeholder="https://example.com"
          className="w-full border p-2 rounded"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />

        <div>
          <label className="text-sm text-gray-600">
            Інтервал перевірки, секунд
          </label>

          <input
            type="number"
            min={30}
            value={interval}
            onChange={(e) => setInterval(Number(e.target.value))}
            className="w-full border p-2 rounded mt-1"
          />

          <div className="text-xs text-gray-400 mt-1">
            Мінімум: 30 секунд
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="text-gray-500"
          >
            Відмінити
          </button>

          <button
            onClick={handleCreate}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            {loading ? "Створення..." : "Створити"}
          </button>
        </div>
      </div>
    </div>
  );
}