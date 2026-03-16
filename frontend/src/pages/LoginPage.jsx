/**
 * Login Page
 * Premium authentication page with two modes:
 * 1. Email + Password login (normal flow)
 * 2. First-time password setup (when employee has no password yet)
 */

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { t, i18n } = useTranslation();
  const { login, setPassword, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Form state
  const [email, setEmail] = useState("");
  const [password, setPasswordValue] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");

  // UI state
  const [mode, setMode] = useState("login"); // "login" | "set-password"
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      // First try with empty password to check if user needs to set one
      if (mode === "login" && !password) {
        const result = await login(email, "");
        if (result.mustSetPassword) {
          setMode("set-password");
          setIsLoading(false);
          return;
        }
      }

      const result = await login(email, password);

      if (result.mustSetPassword) {
        setMode("set-password");
      } else if (result.success) {
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      const msg =
        err.response?.data?.detail || t("auth.invalidCredentials");
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetPassword = async (e) => {
    e.preventDefault();
    setError("");

    if (password.length < 6) {
      setError(t("auth.passwordTooShort"));
      return;
    }

    if (password !== passwordConfirm) {
      setError(t("auth.passwordsDoNotMatch"));
      return;
    }

    setIsLoading(true);
    try {
      const result = await setPassword(email, password, passwordConfirm);
      if (result.success) {
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      const msg = err.response?.data?.detail || t("auth.errorSettingPassword");
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div id="login-page" className="login-page">
      {/* Animated background */}
      <div className="login-bg">
        <div className="login-bg-orb login-bg-orb--1" />
        <div className="login-bg-orb login-bg-orb--2" />
        <div className="login-bg-orb login-bg-orb--3" />
      </div>

      {/* Login card */}
      <div className="login-card">
        {/* Logo section */}
        <div className="login-header">
          <h1 className="login-logo">EvaluAI</h1>
          <p className="login-subtitle">
            {mode === "set-password"
              ? t("auth.createPasswordSubtitle")
              : t("auth.subtitle")}
          </p>
        </div>

        {/* Error display */}
        {error && (
          <div className="login-error" role="alert">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1a7 7 0 100 14A7 7 0 008 1zm-.75 4.25a.75.75 0 011.5 0v3.5a.75.75 0 01-1.5 0v-3.5zM8 11a1 1 0 110 2 1 1 0 010-2z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Login form */}
        {mode === "login" && (
          <form onSubmit={handleLogin} className="login-form">
            <div className="login-field">
              <label htmlFor="login-email" className="login-label">
                {t("auth.email")}
              </label>
              <input
                id="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@scalian.com"
                className="login-input"
                required
                autoFocus
                autoComplete="email"
              />
            </div>

            <div className="login-field">
              <label htmlFor="login-password" className="login-label">
                {t("auth.password")}
              </label>
              <div className="login-password-wrapper">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPasswordValue(e.target.value)}
                  placeholder="••••••••"
                  className="login-input"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="login-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button
              id="login-submit"
              type="submit"
              className="login-button"
              disabled={isLoading || !email}
            >
              {isLoading ? (
                <span className="login-spinner" />
              ) : null}
              {isLoading ? t("auth.loggingIn") : t("auth.login")}
            </button>
          </form>
        )}

        {/* Set password form (first-time login) */}
        {mode === "set-password" && (
          <form onSubmit={handleSetPassword} className="login-form">
            <div className="login-info-banner">
              <span>🔐</span>
              <span>{t("auth.firstTimeMessage")}</span>
            </div>

            <div className="login-field">
              <label className="login-label">{t("auth.email")}</label>
              <input
                type="email"
                value={email}
                className="login-input login-input--readonly"
                readOnly
              />
            </div>

            <div className="login-field">
              <label htmlFor="set-password" className="login-label">
                {t("auth.newPassword")}
              </label>
              <div className="login-password-wrapper">
                <input
                  id="set-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPasswordValue(e.target.value)}
                  placeholder={t("auth.newPasswordPlaceholder")}
                  className="login-input"
                  required
                  minLength={6}
                  autoFocus
                  autoComplete="new-password"
                />
                <button
                  type="button"
                  className="login-toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex={-1}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <div className="login-field">
              <label htmlFor="set-password-confirm" className="login-label">
                {t("auth.confirmPassword")}
              </label>
              <input
                id="set-password-confirm"
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                placeholder={t("auth.confirmPasswordPlaceholder")}
                className="login-input"
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>

            <button
              id="set-password-submit"
              type="submit"
              className="login-button"
              disabled={isLoading || !password || !passwordConfirm}
            >
              {isLoading ? (
                <span className="login-spinner" />
              ) : null}
              {isLoading
                ? t("auth.settingPassword")
                : t("auth.setPasswordButton")}
            </button>

            <button
              type="button"
              className="login-back-link"
              onClick={() => {
                setMode("login");
                setPasswordValue("");
                setPasswordConfirm("");
                setError("");
              }}
            >
              ← {t("auth.backToLogin")}
            </button>
          </form>
        )}

        {/* Language switcher */}
        <div className="login-lang">
          <button
            onClick={() => i18n.changeLanguage("es")}
            className={`login-lang-btn ${i18n.language === "es" ? "login-lang-btn--active" : ""}`}
          >
            🇪🇸 ES
          </button>
          <button
            onClick={() => i18n.changeLanguage("en")}
            className={`login-lang-btn ${i18n.language === "en" ? "login-lang-btn--active" : ""}`}
          >
            🇬🇧 EN
          </button>
        </div>

        {/* Footer */}
        <p className="login-footer">EvaluAI v1.0 — Scalian</p>
      </div>
    </div>
  );
}
