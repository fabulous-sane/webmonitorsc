import { useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";

export default function TelegramConnect() {
  const { user, refreshUser } = useAuth();

  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!waiting) return;

    const interval = setInterval(async () => {
      await refreshUser();
    }, 3000);

    return () => clearInterval(interval);
  }, [waiting]);

  useEffect(() => {
    if (user?.telegram_connected) {
      setWaiting(false);
      setToken(null);
    }
  }, [user]);

  if (!user) return null;

  const handleConnect = async () => {
    setLoading(true);
    setToken(null);

    try {
      const res = await api.post("/telegram/connect");
      const command = res.data.command;
      const token = command.split(" ")[1];
      setToken(token);
      setWaiting(true);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    await api.post("/telegram/disconnect");
    await refreshUser();
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

      {user.telegram_connected && (
        <>
          <div className="bg-green-50 border border-green-200 text-green-700 p-4 rounded-lg flex justify-between items-center">
            <span>Telegram прив'язано</span>
            <span>✅</span>
          </div>

          <button
            onClick={handleDisconnect}
            className="w-full border border-red-300 text-red-600 hover:bg-red-50 py-2 rounded-lg transition"
          >
            Від'єднати Telegram
          </button>
        </>
      )}

      {!user.telegram_connected && !token && (
        <button
          onClick={handleConnect}
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 rounded-lg transition"
        >
          {loading ? "Generating..." : "Connect Telegram"}
        </button>
      )}

      {!user.telegram_connected && token && (
        <>
          <div className="text-sm text-gray-600">
            1. Відкрийте телеграм бот
          </div>

          <a
            href="https://t.me/@TheWebcheckBot"
            target="_blank"
            className="block text-center bg-gray-100 py-2 rounded-lg"
          >
            Відкрити бота
          </a>

          <div className="text-sm text-gray-600">
            2. Відправте команду:
          </div>

          <div className="bg-gray-50 p-3 rounded-lg font-mono text-blue-600 text-center break-all">
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
