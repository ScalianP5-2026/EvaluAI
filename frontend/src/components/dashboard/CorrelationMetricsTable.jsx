/**
 * Correlation Metrics Table Component
 * Displays 5 key AI usage correlations in a structured table
 */

import { useTranslation } from "react-i18next";

export default function CorrelationMetricsTable({ data }) {
  const { t } = useTranslation();

  // Mock correlation data - in production, this would come from backend
  const correlationMetrics = [
    {
      id: 1,
      label: t("correlation.metric1Label"),
      description: t("correlation.metric1Desc"),
      coefficient: 0.34,
      pValue: 0.085,
    },
    {
      id: 2,
      label: t("correlation.metric2Label"),
      description: t("correlation.metric2Desc"),
      coefficient: 0.28,
      pValue: 0.142,
    },
    {
      id: 3,
      label: t("correlation.metric3Label"),
      description: t("correlation.metric3Desc"),
      coefficient: -0.07,
      pValue: 0.518,
    },
    {
      id: 4,
      label: t("correlation.metric4Label"),
      description: t("correlation.metric4Desc"),
      coefficient: 0.15,
      pValue: 0.301,
    },
    {
      id: 5,
      label: t("correlation.metric5Label"),
      description: t("correlation.metric5Desc"),
      coefficient: 0.42,
      pValue: 0.028,
    },
  ];

  const getInterpretation = (coefficient, pValue) => {
    if (pValue > 0.05) {
      return {
        label: t("correlation.noSignificant"),
        color: "text-gray-600 dark:text-gray-400",
      };
    }
    if (Math.abs(coefficient) > 0.5) {
      return {
        label: t("correlation.strong"),
        color: "text-green-600 dark:text-green-400 font-semibold",
      };
    }
    if (Math.abs(coefficient) > 0.3) {
      return {
        label: t("correlation.moderate"),
        color: "text-amber-600 dark:text-amber-400 font-semibold",
      };
    }
    return {
      label: t("correlation.noSignificant"),
      color: "text-gray-600 dark:text-gray-400",
    };
  };

  return (
    <div className="space-y-6">
      {/* Table Header */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="md:col-span-2">
          <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">
            {t("correlation.metric1Label")} / {t("correlation.metric2Label")}
          </h4>
        </div>
        <div>
          <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider text-center">
            {t("correlation.coefficient")}
          </h4>
        </div>
        <div>
          <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider text-center">
            {t("correlation.pValue")}
          </h4>
        </div>
        <div>
          <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider text-center">
            {t("correlation.interpretation")}
          </h4>
        </div>
      </div>

      {/* Metrics Rows */}
      <div className="space-y-4">
        {correlationMetrics.map((metric, idx) => {
          const interpretation = getInterpretation(
            metric.coefficient,
            metric.pValue,
          );
          return (
            <div
              key={metric.id}
              className="grid grid-cols-1 md:grid-cols-5 gap-4 pb-4 md:pb-0 md:border-b md:border-gray-200 dark:md:border-gray-700 last:border-b-0"
            >
              {/* Metric Label & Description */}
              <div className="md:col-span-2">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                  {metric.label}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {metric.description}
                </p>
              </div>

              {/* Coefficient */}
              <div className="text-center">
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {metric.coefficient.toFixed(3)}
                </p>
              </div>

              {/* P-Value */}
              <div className="text-center">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {metric.pValue.toFixed(4)}
                </p>
                {metric.pValue > 0.05 && (
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                    n.s.
                  </p>
                )}
              </div>

              {/* Interpretation */}
              <div className="text-center">
                <p className={`text-sm font-medium ${interpretation.color}`}>
                  {interpretation.label}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Footer */}
      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p className="text-sm text-gray-700 dark:text-gray-300">
          {t("correlation.significanceFooter")}
        </p>
      </div>
    </div>
  );
}
