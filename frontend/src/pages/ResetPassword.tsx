import { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import api from "../api/axios";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [status, setStatus] = useState<"loading" | "form" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setMessage("Посилання на скид не дійсне.");
      return;
    }

    setStatus("form");
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setMessage("Паролі не співпадають.");
      return;
    }

    const token = searchParams.get("token");

    try {
      await api.post("/auth/reset-password", {
        token,
        password,
      });

      setStatus("success");
      setMessage("Пароль успішно оновлено.");
    } catch {
      setStatus("error");
      setMessage("Прострочений або неправильний токен.");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md text-center">

        {status === "loading" && <p>Завантаження...</p>}

        {status === "form" && (
          <form onSubmit={handleSubmit}>
            <h2 className="text-2xl font-bold mb-6">
              Встановити новий пароль
            </h2>

            {message && (
              <div className="mb-4 text-red-600 bg-red-50 p-2 rounded">
                {message}
              </div>
            )}

            <input
              type="password"
              placeholder="Новий пароль"
              className="w-full border p-2 mb-4 rounded"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <input
              type="password"
              placeholder="Підтвердити пароль"
              className="w-full border p-2 mb-6 rounded"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            <button
              type="submit"
              className="w-full bg-blue-600 text-white p-2 rounded"
            >
              Оновити пароль
            </button>
          </form>
        )}

        {status === "success" && (
          <>
            <h2 className="text-green-600 text-xl font-semibold mb-4">
              Успіх
            </h2>
            <p className="mb-6">{message}</p>
            <button
              onClick={() => navigate("/login")}
              className="bg-blue-600 text-white px-4 py-2 rounded"
            >
              До авторизації
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <h2 className="text-red-600 text-xl font-semibold mb-4">
              Помилка
            </h2>
            <p className="mb-6">{message}</p>
            <button
              onClick={() => navigate("/login")}
              className="bg-blue-600 text-white px-4 py-2 rounded"
            >
              Назад до авторизації
            </button>
          </>
        )}
      </div>
    </div>
  );
}
