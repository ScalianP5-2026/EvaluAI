import axios from "axios";

const API_BASE_URL = "/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

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
      console.error("Chat API Error:", error);
      throw error;
    }
  },

  getHistory: async (userId, limit = 10) => {
    try {
      const response = await apiClient.get("/chat/history", {
        params: { user_id: userId, limit },
      });
      return response.data;
    } catch (error) {
      console.error("History API Error:", error);
      throw error;
    }
  },
};

export const kpiAPI = {
  getSummary: async () => {
    try {
      const response = await apiClient.get("/kpi/summary");
      return response.data;
    } catch (error) {
      console.error("KPI API Error:", error);
      throw error;
    }
  },
};

export const healthAPI = {
  checkHealth: async () => {
    try {
      const response = await apiClient.get("/health");
      return response.data;
    } catch (error) {
      console.error("Health Check Error:", error);
      throw error;
    }
  },
};
