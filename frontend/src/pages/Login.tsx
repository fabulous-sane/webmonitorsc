import api from "../api/axios";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [showResend, setShowResend] = useState(false);
  const [resendMessage, setResendMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

    useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setShowResend(false);
    setResendMessage("");
    setLoading(true);

    const success = await login(email, password);

    if (!success) {
      setError("Неправильний логін або пароль");
      setShowResend(true);
      setLoading(false);
      return;
    }

    navigate("/dashboard", { replace: true });
  };

    const handleResend = async () => {
    if (!email) {
      setResendMessage("Введіть вашу пошту.");
      return;
    }

    setResendLoading(true);
    setResendMessage("");

    try {
      await api.post("/auth/resend-confirmation", { email });

      setResendMessage(
        "Якщо акаунт є в системі і не підтверджено, письмо підтвердження було надіслано на пошту."
      );
    } catch {
      setResendMessage(
        "Якщо акаунт є в системі і не підтверджено, письмо підтвердження було надіслано на пошту."
      );
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-xl shadow-md w-full max-w-md"
      >
        <h2 className="text-2xl font-bold mb-6 text-center">
          Авторизація
        </h2>

        {error && (
          <div className="mb-4 text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}

        {resendMessage && (
          <div className="mb-4 text-green-700 bg-green-50 p-2 rounded">
            {resendMessage}
          </div>
        )}

        <input
          type="email"
          placeholder="Електронна пошта"
          className="w-full border p-2 mb-4 rounded"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Пароль"
          className="w-full border p-2 mb-4 rounded"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 transition"
        >
          {loading ? "Виконується вхід..." : "Увійти"}
        </button>

        <div className="mt-2 text-center">
        <button
        type="button"
        onClick={() => navigate("/forgot-password")}
        className="text-sm text-blue-600"
        >
            Забули пароль?
            </button>
        </div>

        {showResend && (
          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={handleResend}
              disabled={resendLoading}
              className="text-sm text-blue-600 hover:underline"
            >
              {resendLoading
                ? "Відправляється..."
                : "Не отримали лист? Відправити лист знову"}
            </button>
          </div>
        )}

        <div className="mt-4 text-center">
          <span className="text-gray-500 text-sm">
            Немає акаунту?
          </span>
          <button
            type="button"
            onClick={() => navigate("/register")}
            className="ml-2 text-blue-600 text-sm"
          >
            Зареєструватися
          </button>
        </div>
      </form>
    </div>
  );
}

