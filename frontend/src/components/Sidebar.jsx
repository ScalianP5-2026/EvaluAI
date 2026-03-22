/**
 * Sidebar Navigation Component
 * Corporate-style sidebar with navy background, gradient overlay
 * Includes logged-in user info and logout button
 */

import { useTranslation } from "react-i18next";
import { useTheme } from "../context/ThemeContext";
import { useAuth } from "../context/AuthContext";
import { Link, useLocation, useNavigate } from "react-router-dom";
import SurveyUpload from "./SurveyUpload";
import { useState } from "react";

export default function Sidebar() {
  const { t, i18n } = useTranslation();
  const { isDark, toggleTheme } = useTheme();
  const { user, logout, isRRHH } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [showCampaignModal, setShowCampaignModal] = useState(false);

  const navItems = [
    { path: "/dashboard", text: t("nav.dashboard") },
    { path: "/chat", text: t("nav.chatbot") },
    { path: "/nlp", text: t("nav.nlp") },
  ];

  const isActive = (path) => location.pathname === path;

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="w-64 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 dark:from-slate-950 dark:via-slate-950 dark:to-slate-900 border-r border-slate-800 h-screen flex flex-col fixed left-0 top-0 shadow-xl">
      {/* Logo Section */}
      <div className="p-8 border-b border-slate-800">
        <h1 className="text-2xl font-bold text-blue-400 tracking-tight">
          FormatIA
        </h1>
        <p className="text-xs text-slate-400 mt-2 font-medium uppercase tracking-widest">
          {t("sidebar.subtitle")}
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`block px-4 py-3 rounded-lg text-sm font-medium transition-all ${
              isActive(item.path)
                ? "bg-blue-600 shadow-lg text-white"
                : "border border-slate-600 text-slate-100 bg-slate-700/60 hover:bg-blue-600 hover:text-white hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-1 focus:ring-offset-slate-900 transition-all duration-200"
            }`}
          >
            {item.text}
          </Link>
        ))}
      </nav>

      {/* RRHH Actions Section */}
      {isRRHH && (
        <div className="p-4 border-t border-slate-800">
          {/* RRHH Actions: visually spaced */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-widest mb-3">
              {t("dashboard.rrhhActionsTitle")}
            </h3>
            <div className="mb-2">
              <SurveyUpload compact={false} />
            </div>
            <button
              className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md"
              type="button"
              onClick={() => setShowCampaignModal(true)}
            >
              <span className="inline-flex items-center gap-2">
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                {t("dashboard.createCampaignButton")}
              </span>
            </button>
          </div>
          {/* Create Campaign Modal */}
          {showCampaignModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
              <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg w-full max-w-xs p-6">
                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                  {t("dashboard.createCampaignButton")}
                </h3>
                <form className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignTitleLabel", "Title")}
                    </label>
                    <input className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignWaveLabel", "Wave")}
                    </label>
                    <input className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700" />
                  </div>
                  <div className="flex justify-end gap-2 mt-2">
                    <button
                      type="button"
                      className="px-4 py-2 text-sm bg-gray-200 dark:bg-slate-700 dark:text-gray-100 rounded-md"
                      onClick={() => setShowCampaignModal(false)}
                    >
                      {t("dashboard.cancel", "Cancel")}
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-sm bg-blue-700 text-white rounded-md"
                    >
                      {t("dashboard.create", "Create")}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Controls Section */}
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center justify-between gap-2">
          <div className="flex gap-1">
            <button
              onClick={() => i18n.changeLanguage("es")}
              className={`w-9 h-9 rounded text-lg font-medium transition-all ${
                i18n.language === "es"
                  ? "bg-blue-600 text-white shadow-lg"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
              }`}
              title="Español"
              aria-label="Español"
              aria-pressed={i18n.language === "es"}
            >
              <span aria-hidden="true">🇪🇸</span>
            </button>
            <button
              onClick={() => i18n.changeLanguage("en")}
              className={`w-9 h-9 rounded text-lg font-medium transition-all ${
                i18n.language === "en"
                  ? "bg-blue-600 text-white shadow-lg"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white"
              }`}
              title="English"
              aria-label="English"
              aria-pressed={i18n.language === "en"}
            >
              <span aria-hidden="true">🇬🇧</span>
            </button>
          </div>

          <button
            onClick={toggleTheme}
            className="w-9 h-9 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white flex items-center justify-center text-lg font-medium transition-all"
            title={isDark ? "Light Mode" : "Dark Mode"}
            aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDark ? "☀️" : "🌙"}
          </button>
        </div>
      </div>

      {/* User Info & Logout */}
      <div className="p-4 border-t border-slate-800">
        {user && (
          <div className="mb-3">
            <p className="text-xs text-slate-400 truncate" title={user.email}>
              {t("auth.loggedInAs")}
            </p>
            <p
              className="text-sm text-slate-200 font-medium truncate"
              title={user.email}
            >
              {user.email}
            </p>
          </div>
        )}
        <button
          id="logout-button"
          onClick={handleLogout}
          className="w-full px-4 py-2 rounded-lg text-sm font-medium border border-red-500/30 text-red-400 bg-red-950/30 hover:bg-red-900/50 hover:text-red-300 hover:border-red-400/50 transition-all duration-200"
        >
          {t("auth.logout")}
        </button>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-500">
          FormatIA v1.0
        </p>
      </div>
    </div>
  );
}
