import axios from "axios";

// ═══════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:9000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Error handler
const handleError = (error, context) => {
  console.error(`${context} Error:`, error);
  throw error;
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
      const response = await apiClient.post("/surveys/upload", formData, {
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