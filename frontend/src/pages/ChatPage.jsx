import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import ChatBox from "../components/Chatbox";
import { chatAPI } from "../services/api";

export default function ChatPage() {
  const { t } = useTranslation();
  const [userId] = useState("1XVWCBPH");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sendError, setSendError] = useState(null);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await chatAPI.getHistory(userId);
      setHistory(data.conversation_history || []);
    } catch (error) {
      console.error("Failed to load history:", error);
    }
  };

  const handleSendMessage = async (message) => {
    setLoading(true);
    setSendError(null);
    try {
      const response = await chatAPI.sendMessage(userId, message);
      setHistory([
        ...history,
        { role: "user", content: message, timestamp: new Date().toISOString() },
        {
          role: "assistant",
          content: response.message,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      console.error("Failed to send message:", error);
      setSendError(t("chat.sendError"));
    } finally {
      setLoading(false);
    }
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
          </div>
        </div>
      </div>
    </div>
  );
}
