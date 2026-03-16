import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import ChatPage from "./pages/ChatPage";
import DashboardPage from "./pages/DashboardPage";
import NLPInsights from "./pages/NLPInsights";

export default function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/login" element={<ChatPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/nlp" element={<NLPInsights />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}
