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
import { useEffect, useRef, useState } from "react";
import { dashboardAPI } from "../services/api";

function useDraggable() {
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const start = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      setOffset({
        x: e.clientX - start.current.x,
        y: e.clientY - start.current.y,
      });
    };

    const onUp = () => {
      dragging.current = false;
      document.body.style.userSelect = "";
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);

    return () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
  }, []);

  const onMouseDown = (e) => {
    dragging.current = true;
    start.current = {
      x: e.clientX - offset.x,
      y: e.clientY - offset.y,
    };
    document.body.style.userSelect = "none";
  };

  const reset = () => setOffset({ x: 0, y: 0 });

  return { offset, onMouseDown, reset };
}

export default function Sidebar() {
  const { t, i18n } = useTranslation();
  const { isDark, toggleTheme } = useTheme();
  const { user, logout, isRRHH } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const campaignDrag = useDraggable();

  const [showCampaignModal, setShowCampaignModal] = useState(false);
  const [campaignTitle, setCampaignTitle] = useState("");
  const [campaignWave, setCampaignWave] = useState("");
  const [campaignDescription, setCampaignDescription] = useState("");
  const [campaignSource, setCampaignSource] = useState("");
  const [campaignFormProvider, setCampaignFormProvider] = useState("");
  const [campaignFormUrl, setCampaignFormUrl] = useState("");
  const [campaignIsActive, setCampaignIsActive] = useState(true);
  const [campaignError, setCampaignError] = useState("");
  const [campaignSuccess, setCampaignSuccess] = useState("");
  const [campaignLoading, setCampaignLoading] = useState(false);

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

  const resetCampaignForm = () => {
    setCampaignTitle("");
    setCampaignWave("");
    setCampaignDescription("");
    setCampaignSource("");
    setCampaignFormProvider("");
    setCampaignFormUrl("");
    setCampaignIsActive(true);
    setCampaignError("");
    setCampaignSuccess("");
  };

  const handleCreateCampaign = async (e) => {
    e.preventDefault();
    setCampaignError("");
    setCampaignSuccess("");

    const title = campaignTitle.trim();
    const wave = campaignWave.trim();

    if (!title && !wave) {
      setCampaignError(t("dashboard.campaignTitleAndWaveRequired"));
      return;
    }

    if (!title) {
      setCampaignError(t("dashboard.campaignTitleRequired"));
      return;
    }

    if (!wave) {
      setCampaignError(t("dashboard.campaignWaveRequired"));
      return;
    }

    setCampaignLoading(true);

    try {
      await dashboardAPI.createCampaign({
        title,
        wave,
        description: campaignDescription.trim(),
        source: campaignSource.trim(),
        form_provider: campaignFormProvider.trim(),
        form_url: campaignFormUrl.trim(),
        is_active: campaignIsActive,
      });

      setCampaignSuccess(
        i18n.language === "es"
          ? "¡Campaña creada exitosamente!"
          : "Campaign created successfully!",
      );

      setCampaignTitle("");
      setCampaignWave("");
      setCampaignDescription("");
      setCampaignSource("");
      setCampaignFormProvider("");
      setCampaignFormUrl("");
      setCampaignIsActive(true);
    } catch (err) {
      setCampaignError(
        i18n.language === "es"
          ? "No se pudo crear campaña"
          : "Could not create campaign",
      );
    } finally {
      setCampaignLoading(false);
    }
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
                : "border border-slate-600 text-slate-100 bg-slate-700/60 hover:bg-blue-600 hover:text-white hover:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-1 focus:ring-offset-slate-900 duration-200"
            }`}
          >
            {item.text}
          </Link>
        ))}
      </nav>

      {/* RRHH Actions Section */}
      {isRRHH && (
        <div className="p-4 border-t border-slate-800">
          <div className="space-y-2">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-widest mb-3">
              {t("dashboard.rrhhActionsTitle")}
            </h3>

            <div className="mb-2">
              <SurveyUpload compact={false} />
            </div>

            <button
              className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md transition-colors"
              type="button"
              onClick={() => {
                setCampaignError("");
                setCampaignSuccess("");
                campaignDrag.reset();
                setShowCampaignModal(true);
              }}
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
            <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40">
              <div
                className="bg-white dark:bg-slate-900 rounded-lg shadow-lg w-full max-w-sm p-6"
                style={{
                  transform: `translate(${campaignDrag.offset.x}px, ${campaignDrag.offset.y}px)`,
                }}
              >
                <div
                  className="flex items-start justify-between mb-4 cursor-grab active:cursor-grabbing select-none"
                  onMouseDown={campaignDrag.onMouseDown}
                >
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {t("dashboard.createCampaignButton")}
                  </h3>
                  <button
                    type="button"
                    onClick={() => {
                      setShowCampaignModal(false);
                      setCampaignError("");
                      setCampaignSuccess("");
                    }}
                    onMouseDown={(e) => e.stopPropagation()}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xl"
                  >
                    ×
                  </button>
                </div>

                <form className="space-y-3" onSubmit={handleCreateCampaign}>
                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignTitleLabel")} *
                    </label>
                    <input
                      className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
                      value={campaignTitle}
                      onChange={(e) => setCampaignTitle(e.target.value)}
                      placeholder={t("dashboard.campaignTitleLabel")}
                      disabled={campaignLoading}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignWaveLabel")} *
                    </label>
                    <input
                      className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
                      value={campaignWave}
                      onChange={(e) => setCampaignWave(e.target.value)}
                      placeholder="t0, t1, t2..."
                      disabled={campaignLoading}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignDescriptionLabel")}
                    </label>
                    <input
                      className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
                      value={campaignDescription}
                      onChange={(e) => setCampaignDescription(e.target.value)}
                      placeholder={t("dashboard.campaignDescriptionLabel")}
                      disabled={campaignLoading}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignSourceLabel")}
                    </label>
                    <input
                      className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
                      value={campaignSource}
                      onChange={(e) => setCampaignSource(e.target.value)}
                      placeholder={t("dashboard.campaignSourceLabel")}
                      disabled={campaignLoading}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignFormProviderLabel")}
                    </label>
                    <input
                      className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
                      value={campaignFormProvider}
                      onChange={(e) => setCampaignFormProvider(e.target.value)}
                      placeholder={t("dashboard.campaignFormProviderLabel")}
                      disabled={campaignLoading}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
                      {t("dashboard.campaignFormUrlLabel")}
                    </label>
                    <input
                      className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
                      value={campaignFormUrl}
                      onChange={(e) => setCampaignFormUrl(e.target.value)}
                      placeholder={t("dashboard.campaignFormUrlLabel")}
                      disabled={campaignLoading}
                    />
                  </div>

                  <div className="flex items-center mt-2">
                    <input
                      id="campaign-is-active"
                      type="checkbox"
                      checked={campaignIsActive}
                      onChange={(e) => setCampaignIsActive(e.target.checked)}
                      disabled={campaignLoading}
                      className="mr-2"
                    />
                    <label
                      htmlFor="campaign-is-active"
                      className="text-xs font-medium text-gray-700 dark:text-gray-200"
                    >
                      {t("dashboard.campaignIsActiveLabel")}
                    </label>
                  </div>

                  {campaignError && (
                    <p className="text-xs text-red-600 dark:text-red-400 font-medium">
                      {campaignError}
                    </p>
                  )}

                  {campaignSuccess && (
                    <div className="flex flex-col gap-2 items-center">
                      <p className="text-xs text-green-600 dark:text-green-400 font-medium">
                        {campaignSuccess}
                      </p>

                      <div className="flex gap-2 mt-2">
                        <button
                          type="button"
                          className="px-4 py-2 text-sm bg-gray-200 dark:bg-slate-700 dark:text-gray-100 rounded-md"
                          onClick={() => {
                            setShowCampaignModal(false);
                            setCampaignSuccess("");
                          }}
                        >
                          {i18n.language === "es" ? "Salir" : "Close"}
                        </button>

                        <button
                          type="button"
                          className="px-4 py-2 text-sm bg-blue-700 text-white rounded-md hover:bg-blue-800 transition-colors"
                          onClick={() => {
                            resetCampaignForm();
                          }}
                        >
                          {i18n.language === "es"
                            ? "Crear otra"
                            : "Create another"}
                        </button>
                      </div>
                    </div>
                  )}

                  {!campaignSuccess && (
                    <div className="flex justify-end gap-2 mt-2">
                      <button
                        type="button"
                        className="px-4 py-2 text-sm bg-gray-200 dark:bg-slate-700 dark:text-gray-100 rounded-md"
                        onClick={() => {
                          resetCampaignForm();
                          setShowCampaignModal(false);
                        }}
                        disabled={campaignLoading}
                      >
                        {t("dashboard.cancel")}
                      </button>

                      <button
                        type="submit"
                        className="px-4 py-2 text-sm bg-blue-700 text-white rounded-md hover:bg-blue-800 transition-colors disabled:opacity-60"
                        disabled={campaignLoading}
                      >
                        {campaignLoading
                          ? t("dashboard.creating") || "Creando..."
                          : t("dashboard.create")}
                      </button>
                    </div>
                  )}
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
