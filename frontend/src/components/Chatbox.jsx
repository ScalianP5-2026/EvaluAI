import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 flex flex-col h-[500px] shadow-sm">
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
              className={`flex w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] px-4 py-3 rounded-xl shadow-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-none"
                    : "bg-gray-50 dark:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-100 dark:border-gray-600 rounded-bl-none"
                }`}
              >
                {/*
                 * NUEVO: Condicional.
                 * Si es el chatbot (no-user), usar ReactMarkdown.
                 * Si es el usuario, pintar texto plano en <p>.
                 */}
                {msg.role === "user" ? (
                  <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                ) : (
                  <div className="text-sm">
                    {/* Mensaje original en Markdown */}
                    <div className="prose dark:prose-invert prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* NUEVO: Información de RAG extraída */}
                    {msg.recommendations && (
                      <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-600 bg-white/50 dark:bg-gray-800/50 p-3 rounded-lg">
                        {msg.recommendations.course && (
                          <div className="mb-3">
                            <span className="flex items-center gap-2 font-semibold text-blue-700 dark:text-blue-400">
                              <span className="text-lg">📚</span> Curso
                              recomendado
                            </span>
                            <p className="mt-1 text-gray-700 dark:text-gray-300 ml-6">
                              {msg.recommendations.course}
                            </p>
                          </div>
                        )}

                        {msg.recommendations.mentor && (
                          <div className="mb-3">
                            <span className="flex items-center gap-2 font-semibold text-purple-700 dark:text-purple-400">
                              <span className="text-lg">👤</span> Mentor
                              sugerido
                            </span>
                            <p className="mt-1 text-gray-700 dark:text-gray-300 ml-6">
                              {msg.recommendations.mentor}
                            </p>
                          </div>
                        )}

                        {msg.recommendations.plan_30_days &&
                          msg.recommendations.plan_30_days.length > 0 && (
                            <div className="mt-3">
                              <span className="flex items-center gap-2 font-semibold text-emerald-700 dark:text-emerald-400">
                                <span className="text-lg">🗓️</span> Plan a 30
                                días
                              </span>
                              <ul className="list-disc mt-2 ml-10 space-y-1 text-gray-700 dark:text-gray-300">
                                {msg.recommendations.plan_30_days.map(
                                  (step, i) => (
                                    <li key={i}>{step}</li>
                                  ),
                                )}
                              </ul>
                            </div>
                          )}
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
