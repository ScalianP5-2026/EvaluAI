import { useState, useEffect } from "react";
import ChatBox from "../components/ChatBox";
import { chatAPI } from "../services/api";

export default function ChatPage() {
  const [userId] = useState("1XVWCBPH"); // Demo user
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

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
      alert("Error sending message. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <ChatBox
          history={history}
          onSendMessage={handleSendMessage}
          loading={loading}
        />
      </div>
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Session Info</h3>
        <div className="space-y-2 text-sm text-slate-600">
          <p>
            <strong>User ID:</strong> {userId}
          </p>
          <p>
            <strong>Messages:</strong> {history.length}
          </p>
          <p>
            <strong>Status:</strong> {loading ? "⏳ Processing..." : "✓ Ready"}
          </p>
        </div>
      </div>
    </div>
  );
}
