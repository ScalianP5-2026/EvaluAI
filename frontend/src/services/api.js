import axios from "axios";

// ═══════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════

const API_BASE_URL =
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_BASE_URL) ||
  "/api/v1";
const NLP_BASE_URL = "/api/nlp";
const VERBOSE_API_ERROR_LOGGING =
  typeof import.meta !== "undefined" &&
  import.meta.env &&
  (import.meta.env.DEV ||
    String(import.meta.env.VITE_VERBOSE_API_ERRORS || "").toLowerCase() ===
      "true");

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

const nlpClient = axios.create({
  baseURL: NLP_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ═══════════════════════════════════════════════════════════════
// Auth Interceptor - Auto-attach JWT token
// ═══════════════════════════════════════════════════════════════

const authInterceptor = (config) => {
  const token = localStorage.getItem("evaluai_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
};

// Apply auth token to both the main API and NLP clients
apiClient.interceptors.request.use(authInterceptor);
nlpClient.interceptors.request.use(authInterceptor);

// Error handler
const handleError = (error, context) => {
  const requestId =
    error?.response?.headers?.["x-request-id"] ||
    error?.response?.headers?.["x-correlation-id"] ||
    null;

  console.error(`${context} Error:`, {
    message: error?.message,
    status: error?.response?.status,
    url: error?.config?.url,
    baseURL: error?.config?.baseURL,
    requestId,
  });

  if (VERBOSE_API_ERROR_LOGGING) {
    console.debug(`${context} Error details:`, {
      responseData: error?.response?.data,
      requestBody: error?.config?.data,
    });
  }

  throw error;
};

// ═══════════════════════════════════════════════════════════════
// Auth API
// ═══════════════════════════════════════════════════════════════

export const authAPI = {
  login: async (email, password) => {
    try {
      const response = await apiClient.post("/auth/login", {
        email,
        password: password || "",
      });
      return response.data;
    } catch (error) {
      handleError(error, "Auth Login");
    }
  },

  setPassword: async (email, password, passwordConfirm) => {
    try {
      const response = await apiClient.post("/auth/set-password", {
        email,
        password,
        password_confirm: passwordConfirm,
      });
      return response.data;
    } catch (error) {
      handleError(error, "Auth Set Password");
    }
  },

  getMe: async () => {
    try {
      const response = await apiClient.get("/auth/me");
      return response.data;
    } catch (error) {
      handleError(error, "Auth Me");
    }
  },
};

// ═══════════════════════════════════════════════════════════════
// Chat API
// ═══════════════════════════════════════════════════════════════

export const chatAPI = {
  sendMessage: async (userId, message, employeeContext) => {
    try {
      const response = await apiClient.post("/chat/query", {
        user_id: userId,
        message,
        employee_context: employeeContext,
      });
      return response.data;
    } catch (error) {
      handleError(error, "Chat");
    }
  },

  getHistory: async (userId, limit = 10) => {
    try {
      const response = await apiClient.get("/chat/history", {
        params: { user_id: userId, limit },
      });
      return response.data;
    } catch (error) {
      handleError(error, "Chat History");
    }
  },
};

// ═══════════════════════════════════════════════════════════════
// Dashboard API
// ═══════════════════════════════════════════════════════════════

export const dashboardAPI = {
  getSummary: async () => {
    try {
      const response = await apiClient.get("/dashboard/summary");
      return response.data;
    } catch (error) {
      handleError(error, "Dashboard");
    }
  },

  uploadSurveys: async (file) => {
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await apiClient.post("/upload/surveys", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return response.data;
    } catch (error) {
      handleError(error, "Upload Surveys");
    }
  },
};

// ═══════════════════════════════════════════════════════════════
// KPI API
// ═══════════════════════════════════════════════════════════════

export const kpiAPI = {
  getSummary: async () => {
    try {
      const response = await apiClient.get("/kpi/summary");
      return response.data;
    } catch (error) {
      handleError(error, "KPI");
    }
  },
};

// ═══════════════════════════════════════════════════════════════
// NLP API
// ═══════════════════════════════════════════════════════════════

export const nlpAPI = {
  getSummary: async () => {
    try {
      const response = await nlpClient.get("/summary");
      return response.data;
    } catch (error) {
      handleError(error, "NLP Summary");
    }
  },

  getStrategicSummary: async () => {
    try {
      const response = await nlpClient.get("/strategic-summary");
      return response.data;
    } catch (error) {
      handleError(error, "NLP Strategic Summary");
    }
  },

  getExecutive: async (lang) => {
    try {
      const response = await nlpClient.get("/executive", {
        params: lang ? { lang } : undefined,
      });
      return response.data;
    } catch (error) {
      handleError(error, "NLP Executive Summary");
    }
  },

  getEmployee: async (employeeId) => {
    try {
      const response = await nlpClient.get(`/employee/${employeeId}`);
      return response.data;
    } catch (error) {
      handleError(error, "NLP Employee Profile");
    }
  },

  analyze: async (payload) => {
    try {
      const response = await apiClient.post("/nlp/analyze", payload);
      return response.data;
    } catch (error) {
      handleError(error, "NLP Analysis");
    }
  },
};

// ═══════════════════════════════════════════════════════════════
// Health Check API
// ═══════════════════════════════════════════════════════════════

export const healthAPI = {
  checkHealth: async () => {
    try {
      const response = await apiClient.get("/health");
      return response.data;
    } catch (error) {
      handleError(error, "Health Check");
    }
  },
};

// ═══════════════════════════════════════════════════════════════
// Export all APIs
// ═══════════════════════════════════════════════════════════════

export const api = {
  chatAPI,
  dashboardAPI,
  kpiAPI,
  nlpAPI,
  healthAPI,
};
