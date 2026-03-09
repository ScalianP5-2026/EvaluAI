import { Link } from "react-router-dom";

export default function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-slate-200">
      <nav className="container mx-auto px-4 py-4 flex items-center justify-between">
        <Link to="/" className="text-2xl font-bold text-indigo-600">
          🤖 EvaluAI
        </Link>
        <div className="flex gap-4">
          <Link to="/" className="btn-secondary">
            💬 Chat
          </Link>
          <Link to="/dashboard" className="btn-secondary">
            📊 Dashboard
          </Link>
        </div>
      </nav>
    </header>
  );
}
