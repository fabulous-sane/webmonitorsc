import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import api from "../api/axios";

export default function ConfirmEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Підтвердження пошти...");

  useEffect(() => {
    const token = searchParams.get("token");

    if (!token) {
      setStatus("error");
      setMessage("Неправильне посилання.");
      return;
    }

    api.post("/auth/confirm-email", { token })
      .then(() => {
        setStatus("success");
        setMessage("Пошту успішно підтверджено.");
      })
      .catch((err) => {
        setStatus("error");

        if (err.response?.status === 400) {
          setMessage("Неправильний або строк токену сплив.");
        } else {
          setMessage("Підтвердження неуспішне.");
        }
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md text-center">
        {status === "loading" && (
          <>
            <h2 className="text-xl font-semibold mb-4">
              Підтвердження...
            </h2>
            <p className="text-gray-500">{message}</p>
          </>
        )}

        {status === "success" && (
          <>
            <h2 className="text-xl font-semibold text-green-600 mb-4">
              Успіх
            </h2>
            <p className="text-gray-600 mb-6">{message}</p>

            <button
              onClick={() => navigate("/login")}
              className="bg-blue-600 text-white px-4 py-2 rounded"
            >
              Перейти до авторизації
            </button>
          </>
        )}

        {status === "error" && (
          <>
            <h2 className="text-xl font-semibold text-red-600 mb-4">
              Error
            </h2>
            <p className="text-gray-600 mb-6">{message}</p>

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
