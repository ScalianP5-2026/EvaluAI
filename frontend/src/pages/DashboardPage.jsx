import { useState, useEffect } from "react";
import KPIDashboard from "../components/KPIDashboard";
import { kpiAPI } from "../services/api";

export default function DashboardPage() {
  const [kpiData, setKpiData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadKPIs();
  }, []);

  const loadKPIs = async () => {
    try {
      setLoading(true);
      const data = await kpiAPI.getSummary();
      setKpiData(data);
      setError(null);
    } catch (err) {
      console.error("Failed to load KPIs:", err);
      setError("Failed to load KPI data");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading KPI data...</div>;
  }

  if (error) {
    return (
      <div className="card bg-red-50 border-red-200 text-red-700">{error}</div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold mb-8">Analytics Dashboard</h1>
      {kpiData && <KPIDashboard data={kpiData} />}
      <button onClick={loadKPIs} className="btn-secondary mt-6">
        Refresh Data
      </button>
    </div>
  );
}
