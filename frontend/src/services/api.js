const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

async function request(path, options = {}, baseUrl = DEFAULT_API_BASE_URL) {
  const response = await fetch(`${baseUrl}${path}`, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed (${response.status})`);
  }
  return response.json();
}

export const api = {
  getDashboardSummary(baseUrl) {
    return request("/dashboard/summary", {}, baseUrl);
  },

  uploadSurveys(file, baseUrl) {
    const formData = new FormData();
    formData.append("file", file);
    return request(
      "/surveys/upload",
      {
        method: "POST",
        body: formData,
      },
      baseUrl
    );
  },

  queryChat(payload, baseUrl) {
    return request(
      "/chat/query",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      baseUrl
    );
  },

  analyzeNlp(payload, baseUrl) {
    return request(
      "/nlp/analyze",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      baseUrl
    );
  },
};
