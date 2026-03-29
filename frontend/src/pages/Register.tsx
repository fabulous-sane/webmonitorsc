import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/axios";

export default function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Паролі не співпадають");
      return;
    }

    setLoading(true);

    try {
      await api.post("/auth/register", { email, password });
      setSuccess(true);
    } catch (err: any) {
      if (err.response?.status === 400) {
        setError("Неправильний формат даних");
      } else if (err.response?.status === 409) {
        setError("Користувач вже існує");
      } else {
        setError("Реєстрація не вдалася");
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md text-center">
          <h2 className="text-2xl font-bold mb-4">
            Перевірте пошту
          </h2>
          <p className="text-gray-600 mb-6">
            Лист із підтвердженням було надіслано.
          </p>

          <button
            onClick={() => navigate("/login")}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            Перейти до авторизації
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-xl shadow-md w-full max-w-md"
      >
        <h2 className="text-2xl font-bold mb-6 text-center">
          Створити акаунт
        </h2>

        {error && (
          <div className="mb-4 text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}

        <input
          type="email"
          placeholder="Електронна пошта"
          className="w-full border p-2 mb-4 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Пароль"
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
          disabled={loading}
          className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition"
        >
          {loading ? "Створення..." : "Зареєструватися"}
        </button>
      </form>
    </div>
  );
}
