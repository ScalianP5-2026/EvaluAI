import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";

export default function ChatBox({ history, onSendMessage, loading }) {
  const { t } = useTranslation();
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSendMessage(input);
      setInput("");
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 flex flex-col h-[48rem] shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        {t("chat.title")}
      </h2>

      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {history.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">
            {t("chat.noMessages")}
          </p>
        ) : (
          history.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-md px-4 py-2 rounded-lg ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                }`}
              >
                <p className="text-sm">{msg.content}</p>

                {msg.role === "assistant" && msg.recommendations && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600 space-y-2">
                    {msg.recommendations.course && (
                      <div className="flex items-start gap-1.5 text-xs">
                        <span>📘</span>
                        <span>
                          <span className="font-semibold">{t("chat.recommendedCourse")}:</span>{" "}
                          {msg.recommendations.course}
                        </span>
                      </div>
                    )}

                    {msg.recommendations.mentor && (
                      <div className="flex items-start gap-1.5 text-xs">
                        <span>👤</span>
                        <span>
                          <span className="font-semibold">{t("chat.recommendedMentor")}:</span>{" "}
                          {msg.recommendations.mentor}
                        </span>
                      </div>
                    )}

                    {msg.recommendations.plan_30_days &&
                      msg.recommendations.plan_30_days.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs font-semibold mb-1">
                            📅 {t("chat.plan30Days")}:
                          </p>
                          <ol className="list-decimal list-inside text-xs space-y-1 ml-1">
                            {msg.recommendations.plan_30_days.map((step, i) => (
                              <li key={i}>{step}</li>
                            ))}
                          </ol>
                        </div>
                      )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t("chat.placeholder")}
          className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 transition-colors font-medium"
        >
          {loading ? "⏳" : "➜"}
        </button>
      </form>
    </div>
  );
}
