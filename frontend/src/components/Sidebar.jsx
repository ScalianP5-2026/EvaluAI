/**
 * Sidebar Navigation Component
 * Corporate-style sidebar with logo, navigation, language, and theme controls
 */

import { useTranslation } from "react-i18next";
import { useTheme } from "../context/ThemeContext";
import { Link, useLocation } from "react-router-dom";
import SurveyUpload from "./SurveyUpload";

export default function Sidebar() {
  const { t, i18n } = useTranslation();
  const { isDark, toggleTheme } = useTheme();
  const location = useLocation();

  const navItems = [
    { path: "/dashboard", text: t("nav.dashboard") },
    { path: "/chat", text: t("nav.chatbot") },
    { path: "/nlp", text: t("nav.nlp") },
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <div className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 h-screen flex flex-col fixed left-0 top-0">
      {/* Logo Section */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-800">
        <h1 className="text-2xl font-bold text-blue-700 dark:text-blue-400">
          EvaluAI
        </h1>
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 font-medium uppercase tracking-wide">
          {t("sidebar.subtitle")}
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`block px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive(item.path)
                ? "bg-blue-50 dark:bg-blue-900 text-blue-700 dark:text-blue-300"
                : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
            }`}
          >
            {item.text}
          </Link>
        ))}
      </nav>

      {/* Upload Section */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <SurveyUpload compact />
      </div>

      {/* Controls Section */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800 space-y-3">
        {/* Language Selector */}
        <div>
          <label className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
            {t("sidebar.language")}
          </label>
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => i18n.changeLanguage("es")}
              className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                i18n.language === "es"
                  ? "bg-blue-700 dark:bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              ES
            </button>
            <button
              onClick={() => i18n.changeLanguage("en")}
              className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                i18n.language === "en"
                  ? "bg-blue-700 dark:bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              EN
            </button>
          </div>
        </div>

        {/* Theme Toggle */}
        <div>
          <label className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
            {t("sidebar.theme")}
          </label>
          <div className="flex gap-2 mt-2">
            <button
              onClick={() => isDark && toggleTheme()}
              className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                !isDark
                  ? "bg-blue-700 dark:bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              ☀️
            </button>
            <button
              onClick={() => !isDark && toggleTheme()}
              className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                isDark
                  ? "bg-blue-700 dark:bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600"
              }`}
            >
              🌙
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-800 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-500">EvaluAI v1.0</p>
      </div>
    </div>
  );
}
