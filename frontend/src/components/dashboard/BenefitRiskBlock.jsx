/**
 * Benefit vs Risk Block Component
 * Executive summary showing Benefit, Risk, and Net Impact scores
 */

import { useTranslation } from "react-i18next";

export default function BenefitRiskBlock({ data }) {
  const { t } = useTranslation();

  const benefitScore = 72;
  const riskScore = 35;
  const netImpact = benefitScore - riskScore;

  const status =
    netImpact > 30 ? "positive" : netImpact > 10 ? "balanced" : "risk";

  const statusConfig = {
    positive: {
      bg: "bg-green-50 dark:bg-green-900/30",
      border: "border-green-200 dark:border-green-800",
      text: "text-green-700 dark:text-green-200",
      label: t("benefit.positiveImpact"),
      description: t("benefit.positiveDesc"),
    },
    balanced: {
      bg: "bg-amber-50 dark:bg-amber-900/30",
      border: "border-amber-200 dark:border-amber-800",
      text: "text-amber-700 dark:text-amber-200",
      label: t("benefit.balanced"),
      description: t("benefit.balancedDesc"),
    },
    risk: {
      bg: "bg-red-50 dark:bg-red-900/30",
      border: "border-red-200 dark:border-red-800",
      text: "text-red-700 dark:text-red-200",
      label: t("benefit.riskStatus"),
      description: t("benefit.riskDesc"),
    },
  };

  const config = statusConfig[status];

  return (
    <div
      className={`${config.bg} ${config.border} border rounded-lg p-8 space-y-6`}
    >
      <div className="flex items-start justify-between">
        <div>
          <h3 className={`text-lg font-semibold ${config.text}`}>
            {config.label}
          </h3>
          <p className={`text-sm mt-1 ${config.text} opacity-75`}>
            {config.description}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className={`${config.bg} p-4 rounded-lg border ${config.border}`}>
          <p className={`text-xs font-medium ${config.text} opacity-75`}>
            {t("benefit.benefitScore")}
          </p>
          <p className={`text-3xl font-bold ${config.text} mt-2`}>
            {benefitScore}
          </p>
        </div>
        <div className={`${config.bg} p-4 rounded-lg border ${config.border}`}>
          <p className={`text-xs font-medium ${config.text} opacity-75`}>
            {t("benefit.riskScore")}
          </p>
          <p className={`text-3xl font-bold ${config.text} mt-2`}>
            {riskScore}
          </p>
        </div>
        <div className={`${config.bg} p-4 rounded-lg border ${config.border}`}>
          <p className={`text-xs font-medium ${config.text} opacity-75`}>
            {t("benefit.netImpact")}
          </p>
          <p className={`text-3xl font-bold ${config.text} mt-2`}>
            +{netImpact}
          </p>
        </div>
      </div>
    </div>
  );
}
