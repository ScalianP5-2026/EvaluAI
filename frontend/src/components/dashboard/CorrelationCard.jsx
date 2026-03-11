/**
 * Correlation Card Component
 * Displays AI usage vs digital self-efficacy correlation with strategic insights
 */

import { useTranslation } from "react-i18next";

export default function CorrelationCard({ data }) {
  const { t } = useTranslation();

  if (!data?.ai_usage_correlation) {
    return <div className="text-gray-400 dark:text-gray-500">{t("common.noData")}</div>;
  }

  const correlation = data.ai_usage_correlation.correlation;
  const pValue = data.ai_usage_correlation.p_value;

  let correlationStatus = "no-significant";
  if (Math.abs(correlation) > 0.5) {
    correlationStatus = "strong";
  } else if (Math.abs(correlation) > 0.3) {
    correlationStatus = "moderate";
  }

  const insights = {
    "no-significant": {
      label: t("correlation.noSignificant"),
      description: t("correlation.noSigDescription"),
      action: t("correlation.noSigAction"),
    },
    moderate: {
      label: t("correlation.moderate"),
      description: t("correlation.moderateDescription"),
      action: t("correlation.moderateAction"),
    },
    strong: {
      label: t("correlation.strong"),
      description: t("correlation.strongDescription"),
      action: t("correlation.strongAction"),
    },
  };

  const insight = insights[correlationStatus];

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {t("correlation.insight")}
        </h4>
        <p className="text-gray-700 dark:text-gray-300 text-sm">
          {insight.label}
        </p>
        <p className="text-gray-600 dark:text-gray-400 text-sm mt-2">
          {insight.description}
        </p>
      </div>

      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
          {t("correlation.recommendation")}
        </h4>
        <p className="text-sm text-blue-800 dark:text-blue-300">
          {insight.action}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-600 dark:text-gray-400 font-medium">
            {t("correlation.coefficientLabel")}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {correlation.toFixed(3)}
          </p>
        </div>
        <div>
          <p className="text-gray-600 dark:text-gray-400 font-medium">
            {t("correlation.pValueLabel")}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {pValue.toFixed(4)}
          </p>
        </div>
      </div>
    </div>
  );
}
