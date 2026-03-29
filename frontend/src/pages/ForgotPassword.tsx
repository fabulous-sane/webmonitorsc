import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";

export default function ForgotPassword() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      await api.post("/auth/forgot-password", { email });
    } catch {

    } finally {
      setLoading(false);
      setMessage(
        "Якщо акаунт є в системі, письмо з відновленням паролю було надіслано."
      );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-xl shadow-md w-full max-w-md"
      >
        <h2 className="text-2xl font-bold mb-6 text-center">
          Скинути пароль
        </h2>

        {message && (
          <div className="mb-4 text-green-700 bg-green-50 p-2 rounded">
            {message}
          </div>
        )}

        <input
          type="email"
          placeholder="Введіть ел. пошту"
          className="w-full border p-2 mb-4 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white p-2 rounded"
        >
          {loading ? "Відправка..." : "Отримати посилання на відновлення"}
        </button>

        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={() => navigate("/login")}
            className="text-sm text-blue-600"
          >
            Назад до авторизації
          </button>
        </div>
      </form>
    </div>
  );
}
