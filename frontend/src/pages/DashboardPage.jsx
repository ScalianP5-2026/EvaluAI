import { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import KPIDashboard from "../components/KPIDashboard";
import SectionHeader from "../components/ui/SectionHeader";
import { kpiAPI } from "../services/api";

export default function DashboardPage() {
  const { t } = useTranslation();
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
      const serverMessage =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message;
      setError(serverMessage || t("dashboard.loadError"));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-pulse text-gray-500 dark:text-gray-400">
          {t("dashboard.loading")}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-200 rounded-lg p-4">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <SectionHeader title={t("dashboard.title")} />
      {kpiData && <KPIDashboard data={kpiData} />}
      <div className="mt-8 text-center">
        <button
          onClick={loadKPIs}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 dark:bg-blue-600 dark:hover:bg-blue-700 rounded-md transition-colors"
        >
          {t("dashboard.refreshData")}
        </button>
      </div>
    </div>
  );
}
