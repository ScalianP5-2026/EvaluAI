/**
 * Reusable KPI Card Component
 * Displays a single KPI metric with value, label, and status indicator
 */

import { useTranslation } from "react-i18next";

export default function KpiCard({ label, value, status, icon: Icon }) {
  const { t } = useTranslation();

  const statusColors = {
    positive:
      "bg-green-50 border-green-200 text-green-700 dark:bg-green-900/40 dark:border-green-800 dark:text-green-100",
    moderate:
      "bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-900/40 dark:border-amber-800 dark:text-amber-100",
    risk: "bg-red-50 border-red-200 text-red-700 dark:bg-red-900/40 dark:border-red-800 dark:text-red-100",
  };

  const statusValue = status || "moderate";

  const statusLabel = {
    positive: t("kpi.statusHealthy"),
    moderate: t("kpi.statusMonitor"),
    risk: t("kpi.statusAlert"),
  }[statusValue];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">
            {label}
          </p>
          <p className="text-3xl font-semibold text-gray-900 dark:text-white">
            {value}
          </p>
        </div>
        {Icon && (
          <div className={`p-3 rounded-lg border ${statusColors[statusValue]}`}>
            <Icon className="w-6 h-6" />
          </div>
        )}
      </div>
      <div
        className={`mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-xs font-medium px-2 py-1 rounded ${statusColors[statusValue]}`}
      >
        {t("kpi.statusLabel")}: {statusLabel}
      </div>
    </div>
  );
}
