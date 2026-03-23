import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import ChatBox from "../components/Chatbox";
import { chatAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function ChatPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const userId = user?.employee_id || "1XVWCBPH";
  const initialHistory = [
    {
      role: "assistant",
      content: t("chat.welcomeMessage"),
      timestamp: new Date().toISOString(),
    },
  ];
  const [history, setHistory] = useState(initialHistory);
  const [loading, setLoading] = useState(false);
  const [sendError, setSendError] = useState(null);
  const [latestInsights, setLatestInsights] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await chatAPI.getHistory(userId);
      // OJO AL FIX: chatAPI.getHistory devuelve un Array directo según FastAPI [ {role, content, timestamp} ]
      // NO un objeto con { conversation_history: [...] }

      if (Array.isArray(data) && data.length > 0) {
        // Formateamos los datos asegurando que respeten el formato del estado
        const formattedHistory = data
          .map((turn) => ({
            role: turn.role,
            content: turn.content,
            recommendations: turn.recommendations || null,
            timestamp: turn.timestamp || new Date().toISOString(),
          }))
          .reverse(); // Supabase los trae desc (novedad arriba), queremos asc (novedad abajo)

        // FIX: Ya no empujamos el [initialHistory[0], ...]
        // Simplemente cargamos la conversación ininterrumpida que traemos del backend.
        setHistory([...formattedHistory]);
      } else {
        // Solo mandamos el mensaje de bienvenida "Hola..." si es un usuario totalmente nuevo
        // sin ninguna iteración en Supabase.
        setHistory(initialHistory);
      }
    } catch (error) {
      console.error("Failed to load history:", error);
    }
  };

  const handleSendMessage = async (message) => {
    setLoading(true);
    setSendError(null);
    try {
      const response = await chatAPI.sendMessage(userId, message);

      // Añadimos este pequeño limpiador de resiliencia:
      let cleanMessage = response.message;
      if (cleanMessage.startsWith("{") && cleanMessage.includes('"message":')) {
        try {
          // Intentar extraer el mensaje si vino corrompido dentro de un string JSON parcial
          const regex = /"message"\s*:\s*"([^"]+)"/;
          const match = cleanMessage.match(regex);
          if (match && match[1]) {
            cleanMessage = match[1];
          }
        } catch (e) {
          console.log("No se pudo limpiar el mensage feo");
        }
      }

      setHistory((prevHistory) => [
        ...prevHistory,
        { role: "user", content: message, timestamp: new Date().toISOString() },
        {
          role: "assistant",
          content: cleanMessage, // Usar el texto limpio
          recommendations: response.recommendations,
          insights: response.insights,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      console.error("Failed to send message:", error);
      setSendError(t("chat.sendError"));
    } finally {
      setLoading(false);
    }
    setLatestInsights(response.insights);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {sendError && (
        <div className="mb-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg px-4 py-3 text-sm">
          {sendError}
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChatBox
            history={history}
            onSendMessage={handleSendMessage}
            loading={loading}
          />
          {sendError && (
            <p
              role="alert"
              className="mt-2 text-sm text-red-600 dark:text-red-400"
            >
              {sendError}
            </p>
          )}
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {t("chat.sessionInfo")}
          </h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400 font-medium">
                {t("chat.userId")}:
              </span>
              <span className="text-gray-900 dark:text-white font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                {userId}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500 dark:text-gray-400 font-medium">
                {t("chat.messages")}:
              </span>
              <span className="text-gray-900 dark:text-white font-semibold">
                {history.length}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400 font-medium">
                {t("chat.status")}:
              </span>
              <span
                className={`text-xs font-medium px-2 py-1 rounded-full ${
                  loading
                    ? "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300"
                    : "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300"
                }`}
              >
                {loading ? t("chat.processing") : t("chat.ready")}
              </span>
            </div>

            {/* NUEVA CAJA: INSIGHTS DE GEMINI */}
            {latestInsights && (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 shadow-sm">
                <h3 className="text-lg font-semibold text-blue-600 dark:text-blue-400 mb-4 flex items-center gap-2">
                  <span>🧠</span> IA Insights
                </h3>

                <div className="space-y-4 text-sm">
                  {latestInsights.personal && (
                    <div>
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
                        Análisis Personal
                      </p>
                      <p className="text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700/50 p-3 rounded">
                        {latestInsights.personal}
                      </p>
                    </div>
                  )}

                  {latestInsights.department && (
                    <div>
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
                        Tendencia de tu Departamento
                      </p>
                      <p className="text-gray-700 dark:text-gray-300">
                        {latestInsights.department}
                      </p>
                    </div>
                  )}

                  {latestInsights.general && (
                    <div>
                      <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-1">
                        Panorama Global
                      </p>
                      <p className="text-gray-700 dark:text-gray-300 italic">
                        {latestInsights.general}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
