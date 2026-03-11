/**
 * Executive Snapshot Component
 * Clean, minimal KPI display for executives
 */

import { useTranslation } from "react-i18next";

function SnapshotKPI({ title, value, status, description, statusLabel }) {
  const statusColors = {
    healthy: "border-l-4 border-green-500",
    monitor: "border-l-4 border-amber-500",
    alert: "border-l-4 border-red-500",
  };

  const statusBadge = {
    healthy: "bg-green-50 dark:bg-green-900 text-green-700 dark:text-green-200",
    monitor: "bg-amber-50 dark:bg-amber-900 text-amber-700 dark:text-amber-200",
    alert: "bg-red-50 dark:bg-red-900 text-red-700 dark:text-red-200",
  };

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg p-6 ${statusColors[status]} shadow-sm hover:shadow-md transition-shadow`}
    >
      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">
        {title}
      </p>
      <p className="text-4xl font-bold text-gray-900 dark:text-white mt-2">
        {value}
      </p>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
        {description}
      </p>
      <div
        className={`inline-block px-2.5 py-1 rounded text-xs font-medium mt-3 ${statusBadge[status]}`}
      >
        {statusLabel[status]}
      </div>
    </div>
  );
}

export default function ExecutiveSnapshot({ data }) {
  const { t } = useTranslation();

  if (!data) return null;

  // Calculate metrics

  // Adoption rate: frequency-based (frequent + very_frequent / total)
  // This is the single adoption definition used across the entire dashboard.
  const motionByUsage = data.motivation_by_usage || {};
  const usageTotal =
    Object.values(motionByUsage).reduce((s, v) => s + (v.count ?? 0), 0);
  const freqCount =
    (motionByUsage["4_frequent"]?.count ?? 0) +
    (motionByUsage["5_very_frequent"]?.count ?? 0);
  const adoptionRate =
    usageTotal > 0 ? Math.round((freqCount / usageTotal) * 100) : 0;

  const dependencyRisk = data.dependency_risk
    ? Math.round(
        (data.dependency_risk.medium_risk /
          (data.dependency_risk.high_risk +
            data.dependency_risk.medium_risk +
            data.dependency_risk.low_risk)) *
          100,
      )
    : 0;

  const statusLabels = {
    healthy: t("kpi.statusHealthy"),
    monitor: t("kpi.statusMonitor"),
    alert: t("kpi.statusAlert"),
  };

  const kpis = [
    {
      title: t("executive.trainingAdoption"),
      value: `${adoptionRate}%`,
      status:
        adoptionRate > 60
          ? "healthy"
          : adoptionRate >= 30
            ? "monitor"
            : "alert",
      description: t("executive.trainingAdoptionDesc"),
    },
    {
      title: t("executive.aiUsageIntensity"),
      value: "42%",
      status: "monitor",
      description: t("executive.aiUsageIntensityDesc"),
    },
    {
      title: t("executive.employeeMotivation"),
      value: "3.95/5",
      status: "healthy",
      description: t("executive.employeeMotivationDesc"),
    },
    {
      title: t("executive.dependencyRiskLevel"),
      value: `${dependencyRisk}%`,
      status: dependencyRisk > 50 ? "monitor" : "healthy",
      description: t("executive.dependencyRiskDesc"),
    },
  ];

  return (
    <div className="mb-12">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
        {t("executive.snapshot")}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <SnapshotKPI
            key={idx}
            title={kpi.title}
            value={kpi.value}
            status={kpi.status}
            description={kpi.description}
            statusLabel={statusLabels}
          />
        ))}
      </div>
    </div>
  );
}
