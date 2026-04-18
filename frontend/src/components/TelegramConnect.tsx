import { useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function TelegramConnect() {
  const { user, refreshUser } = useAuth();
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (!waiting) return;

    let attempts = 0;

    const interval = setInterval(async () => {
      attempts++;

      const ok = await refreshUser();

      if (!ok) {
    clearInterval(interval);
    setWaiting(false);
    setToken(null);
    setError("Сесія втрачена. Увійдіть знову.");

    setTimeout(() => {
    navigate("/login")
    }, 1500);

    return;
    }

      if (attempts >= 20) {
        clearInterval(interval);
        setWaiting(false);
        setToken(null);
        setError("Не вдалося підключити Telegram");
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [waiting]);

  useEffect(() => {
    if (user?.telegram_connected) {
      setWaiting(false);
      setToken(null);
      setError(null);
    }
  }, [user]);

  if (!user) return null;

  const handleConnect = async () => {
    setLoading(true);
    setToken(null);
    setError(null);

    try {
      const res = await api.post("/telegram/connect");
      const token = res.data.command?.split(" ")[1] ?? null;

      if (!token) {
        setError("Невалідна відповідь сервера");
        return;
      }

      setToken(token);
      setWaiting(true);
    } catch {
      setError("Помилка підключення Telegram");
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    try {
      await api.post("/telegram/disconnect");
      await refreshUser();
    } catch {
      setError("Не вдалося від'єднати Telegram");
    }
  };

  const copyCommand = async () => {
    if (!token) return;
    await navigator.clipboard.writeText(`/connect ${token}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 space-y-4">
      <h3 className="text-lg font-semibold">Прив'язка до Telegram</h3>

      {error && (
        <div className="text-red-600 text-sm text-center">{error}</div>
      )}

      {user.telegram_connected && (
        <>
          <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-lg flex justify-between items-center">
            <span>Telegram прив'язано</span>
            <span>✅</span>
          </div>

          <button
            onClick={handleDisconnect}
            className="w-full border border-red-300 text-red-600 hover:bg-red-50 py-2 rounded-lg"
          >
            Від'єднати Telegram
          </button>
        </>
      )}

      {!user.telegram_connected && !token && (
        <button
          onClick={handleConnect}
          disabled={loading || waiting}
          className="w-full bg-blue-600 text-white py-2 rounded-lg"
        >
          {loading ? "Генерується..." : "Connect Telegram"}
        </button>
      )}

      {!user.telegram_connected && token && (
        <>
          <div className="text-sm text-gray-600">
            1. Відкрийте телеграм бот
          </div>

          <a
            href="https://t.me/TheWebcheckBot"
            target="_blank"
            className="block text-center bg-gray-100 py-2 rounded-lg"
          >
            Відкрити бота
          </a>

          <div className="text-sm text-gray-600">
            2. Відправте команду:
          </div>

          <div className="bg-gray-50 p-3 rounded-lg font-mono text-blue-600 text-center">
            /connect {token}
          </div>

          <button
            onClick={copyCommand}
            className="w-full border border-gray-300 py-2 rounded-lg"
          >
            {copied ? "Скопійовано ✓" : "Скопіювати команду"}
          </button>

          {waiting && (
            <div className="text-sm text-gray-500 text-center animate-pulse">
              Очікується підтвердження...
            </div>
          )}
        </>
      )}
    </div>
  );
}