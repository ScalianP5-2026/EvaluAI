import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "./services/api";

const DEFAULT_API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const AI_USAGE_LEVELS = [
  "never",
  "rarely",
  "sometimes",
  "frequently",
  "always",
];

const ROLES = [
  "Data Analyst",
  "Technology",
  "HR",
  "Finance",
  "Operations",
  "Marketing",
  "Sales",
];

function DashboardPanel({ dashboard, loading, error, onRefresh }) {
  if (loading) {
    return <p className="status-card">Loading dashboard...</p>;
  }

  if (error) {
    return (
      <div className="status-card status-error">
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={onRefresh}>
          Retry
        </button>
      </div>
    );
  }

  if (!dashboard) {
    return <p className="status-card">No dashboard data loaded yet.</p>;
  }

  const usageData = dashboard.usage_distribution || [];
  const genderData = dashboard.gender_distribution || [];
  const departmentData = dashboard.department_distribution || [];
  const primaryToolData = dashboard.primary_tool_distribution || [];
  const aiToolUsageData = dashboard.ai_tools_usage || [];

  const normalizeItems = (items) =>
    items.map((item) => ({
      label: item.level || item.label || "Unknown",
      count: Number(item.count) || 0,
    }));

  const renderDistribution = (title, items) => {
    const normalizedItems = normalizeItems(items);
    const maxCount = Math.max(...normalizedItems.map((item) => item.count), 1);
    return (
      <article className="card">
        <h3>{title}</h3>
        {normalizedItems.length === 0 ? (
          <p>No data available</p>
        ) : (
          <ul className="usage-list">
            {normalizedItems.map((item) => (
              <li key={`${title}-${item.label}`}>
                <span>{item.label}</span>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${(item.count / maxCount) * 100}%` }}
                  />
                </div>
                <strong>{item.count}</strong>
              </li>
            ))}
          </ul>
        )}
      </article>
    );
  };

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Dashboard de analisis</h2>
        <button className="btn btn-secondary" onClick={onRefresh}>
          Refresh
        </button>
      </div>

      <div className="stats-grid">
        <article>
          <h3>Employees</h3>
          <p>{dashboard.total_employees}</p>
        </article>
        <article>
          <h3>Avg motivation</h3>
          <p>{dashboard.avg_motivation}</p>
        </article>
        <article>
          <h3>Avg self efficacy</h3>
          <p>{dashboard.avg_self_efficacy}</p>
        </article>
        <article>
          <h3>Avg AI use score</h3>
          <p>{dashboard.avg_ai_use_score}</p>
        </article>
        <article>
          <h3>Avg age</h3>
          <p>{dashboard.avg_age}</p>
        </article>
        <article>
          <h3>Avg AI integration</h3>
          <p>{dashboard.avg_ai_integration}</p>
        </article>
        <article>
          <h3>Human vs AI preference</h3>
          <p>{dashboard.avg_human_preference}</p>
        </article>
      </div>

      <div className="panel-grid">
        {renderDistribution("AI usage distribution", usageData)}
        {renderDistribution("AI tools adoption", aiToolUsageData)}
      </div>

      <div className="panel-grid">
        {renderDistribution("Gender distribution", genderData)}
        {renderDistribution("Department distribution", departmentData)}
      </div>

      <div className="panel-grid">
        {renderDistribution("Primary tool distribution", primaryToolData)}
        <article className="card">
          <h3>Correlations</h3>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                {(dashboard.correlations || []).map((item) => (
                  <tr key={item.metric}>
                    <td>{item.metric}</td>
                    <td>{item.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>
      </div>

      <article className="card">
        <h3>Auto insights</h3>
        <ul className="plain-list">
          {(dashboard.insights || []).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}

function ChatbotPanel({ apiBaseUrl }) {
  const [form, setForm] = useState({
    employee_role: "Technology",
    learning_goal: "Python avanzado para ML",
    ai_usage: "sometimes",
    self_efficacy: 6.5,
    motivation: 7.0,
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const onSliderChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: Number(value) }));
  };

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await api.queryChat(form, apiBaseUrl);
      setResult(payload);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h2>Chatbot inteligente</h2>
      <p className="panel-subtitle">
        Recommendation assistant for personalized learning plans.
      </p>

      <form className="form-grid" onSubmit={onSubmit}>
        <label>
          Employee role
          <select name="employee_role" value={form.employee_role} onChange={onChange}>
            {ROLES.map((role) => (
              <option key={role} value={role}>
                {role}
              </option>
            ))}
          </select>
        </label>

        <label>
          Learning goal
          <input
            name="learning_goal"
            value={form.learning_goal}
            onChange={onChange}
            required
          />
        </label>

        <label>
          Current AI usage
          <select name="ai_usage" value={form.ai_usage} onChange={onChange}>
            {AI_USAGE_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </label>

        <label>
          Self efficacy: {form.self_efficacy.toFixed(1)}
          <input
            type="range"
            min="1"
            max="10"
            step="0.1"
            name="self_efficacy"
            value={form.self_efficacy}
            onChange={onSliderChange}
          />
        </label>

        <label>
          Motivation: {form.motivation.toFixed(1)}
          <input
            type="range"
            min="1"
            max="10"
            step="0.1"
            name="motivation"
            value={form.motivation}
            onChange={onSliderChange}
          />
        </label>

        <button className="btn" type="submit" disabled={loading}>
          {loading ? "Thinking..." : "Ask assistant"}
        </button>
      </form>

      {error && <p className="status-card status-error">{error}</p>}

      {result && (
        <div className="panel-stack">
          <article className="card">
            <h3>Message</h3>
            <p>{result.message}</p>
          </article>

          <article className="card">
            <h3>Recommended courses</h3>
            <ul className="plain-list">
              {(result.recommended_courses || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>

          <article className="card">
            <h3>Recommended mentor</h3>
            <p>{result.recommended_mentor || "No mentor found"}</p>
          </article>

          <article className="card">
            <h3>30-day plan</h3>
            <ul className="plain-list">
              {(result.thirty_day_plan || []).map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </article>

          <article className="card accent">
            Estimated improvement for similar profiles:{" "}
            {result.similar_profile_improvement}%
          </article>
        </div>
      )}
    </section>
  );
}

function NlpPanel({ apiBaseUrl }) {
  const [rawComments, setRawComments] = useState(
    "Good support from mentor\nTraining was hard and confusing\nUseful prompts saved time"
  );
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const comments = useMemo(
    () => rawComments.split("\n").map((line) => line.trim()).filter(Boolean),
    [rawComments]
  );

  const onAnalyze = async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await api.analyzeNlp({ comments }, apiBaseUrl);
      setResult(payload);
    } catch (analysisError) {
      setError(analysisError.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <h2>NLP opinion analyzer</h2>
      <label>
        Paste one comment per line
        <textarea
          rows={7}
          value={rawComments}
          onChange={(event) => setRawComments(event.target.value)}
        />
      </label>

      <button className="btn" onClick={onAnalyze} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze comments"}
      </button>

      {error && <p className="status-card status-error">{error}</p>}

      {result && (
        <div className="panel-stack">
          <div className="stats-grid stats-grid-2">
            <article>
              <h3>Overall sentiment</h3>
              <p>{result.overall_sentiment}</p>
            </article>
            <article>
              <h3>Sentiment score</h3>
              <p>{result.sentiment_score}</p>
            </article>
          </div>

          <article className="card">
            <h3>Topics</h3>
            {(result.topics || []).length === 0 ? (
              <p>No topics detected</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Topic</th>
                      <th>Matches</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.topics.map((topic) => (
                      <tr key={topic.topic}>
                        <td>{topic.topic}</td>
                        <td>{topic.matches}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="card">
            <h3>Group recommendations</h3>
            <ul className="plain-list">
              {(result.group_recommendations || []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [apiBaseUrl, setApiBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadError, setUploadError] = useState("");
  const [activeTab, setActiveTab] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState("");

  const loadDashboard = useCallback(async () => {
    setDashboardLoading(true);
    setDashboardError("");
    try {
      const payload = await api.getDashboardSummary(apiBaseUrl);
      setDashboard(payload);
    } catch (error) {
      setDashboardError(error.message);
    } finally {
      setDashboardLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const handleUpload = async () => {
    if (!file) {
      setUploadError("Select a CSV file first.");
      setUploadStatus("");
      return;
    }

    setUploadError("");
    setUploadStatus("Uploading...");

    try {
      const payload = await api.uploadSurveys(file, apiBaseUrl);
      setUploadStatus(payload.message || "Dataset updated");
      await loadDashboard();
    } catch (error) {
      setUploadStatus("");
      setUploadError(error.message);
    }
  };

  return (
    <div className="app-shell">
      <aside className="control-panel">
        <h1>EvaluAI</h1>
        <p>Dashboard + Chatbot + NLP analyzer</p>

        <label>
          API base URL
          <input
            value={apiBaseUrl}
            onChange={(event) => setApiBaseUrl(event.target.value)}
          />
        </label>

        <label>
          Upload survey CSV
          <input
            type="file"
            accept=".csv"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
        </label>

        <button className="btn" onClick={handleUpload}>
          Send CSV to API
        </button>

        {uploadStatus && <p className="status-card status-ok">{uploadStatus}</p>}
        {uploadError && <p className="status-card status-error">{uploadError}</p>}

        <nav className="tab-list">
          <button
            className={activeTab === "dashboard" ? "tab tab-active" : "tab"}
            onClick={() => setActiveTab("dashboard")}
          >
            1) Dashboard de analisis
          </button>
          <button
            className={activeTab === "chatbot" ? "tab tab-active" : "tab"}
            onClick={() => setActiveTab("chatbot")}
          >
            2) Chatbot inteligente
          </button>
          <button
            className={activeTab === "nlp" ? "tab tab-active" : "tab"}
            onClick={() => setActiveTab("nlp")}
          >
            3) NLP opinion analyzer
          </button>
        </nav>
      </aside>

      <main className="content-area">
        {activeTab === "dashboard" && (
          <DashboardPanel
            dashboard={dashboard}
            loading={dashboardLoading}
            error={dashboardError}
            onRefresh={loadDashboard}
          />
        )}
        {activeTab === "chatbot" && <ChatbotPanel apiBaseUrl={apiBaseUrl} />}
        {activeTab === "nlp" && <NlpPanel apiBaseUrl={apiBaseUrl} />}
      </main>
    </div>
  );
}
