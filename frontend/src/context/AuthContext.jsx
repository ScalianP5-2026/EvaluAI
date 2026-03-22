/**
 * Authentication Context
 * Manages user session state, login/logout, and JWT token persistence.
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() =>
    localStorage.getItem("evaluai_token"),
  );
  const [loading, setLoading] = useState(true);

  // Restore session from stored token on mount
  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem("evaluai_token");
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const userData = await authAPI.getMe();
        setUser(userData);
        setToken(storedToken);
      } catch (error) {
        console.warn("Session expired, clearing token");
        localStorage.removeItem("evaluai_token");
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = useCallback(async (email, password) => {
    const response = await authAPI.login(email, password);

    // Check if this is a first-time login (must set password)
    if (response.must_set_password) {
      return { mustSetPassword: true, email: response.email };
    }

    // Normal login - store token and user info
    localStorage.setItem("evaluai_token", response.access_token);
    setToken(response.access_token);
    setUser(response.employee);
    return { success: true };
  }, []);

  const setPassword = useCallback(async (email, password, passwordConfirm) => {
    const response = await authAPI.setPassword(
      email,
      password,
      passwordConfirm,
    );

    // Auto-login after setting password
    localStorage.setItem("evaluai_token", response.access_token);
    setToken(response.access_token);
    setUser(response.employee);
    return { success: true };
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("evaluai_token");
    setToken(null);
    setUser(null);
  }, []);

  // Helper: is RRHH (by department, case-insensitive)
  // Helper: is RRHH (robust, case-insensitive, allows common variants)
  const isRRHH = (() => {
    if (!user || !user.department || typeof user.department !== "string")
      return false;
    const dep = user.department.trim().toLowerCase();
    // Accept: "rrhh", "recursos humanos", "human resources", etc.
    return ["rrhh", "recursos humanos", "human resources", "hr"].some(
      (variant) =>
        dep === variant ||
        dep.replace(/\s+/g, "") === variant.replace(/\s+/g, ""),
    );
  })();

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user && !!token,
    department: user?.department || null,
    isRRHH,
    login,
    setPassword,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export default AuthContext;
