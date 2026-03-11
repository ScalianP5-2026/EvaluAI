/**
 * Executive KPI Cards Component
 * Displays 5 key performance indicators in a responsive grid
 */

import { useTranslation } from "react-i18next";
import KpiCard from "../ui/KpiCard";

export default function ExecutiveKPICards({ data }) {
  const { t } = useTranslation();

  if (!data) return null;

  // Calculate KPI scores
  const acceptanceRate = data.acceptance_distribution
    ? Math.round(
        ((data.acceptance_distribution.high +
          data.acceptance_distribution.very_high) /
          (data.acceptance_distribution.very_low +
            data.acceptance_distribution.low +
            data.acceptance_distribution.medium +
            data.acceptance_distribution.high +
            data.acceptance_distribution.very_high)) *
          100,
      )
    : 0;

  const kpis = [
    {
      label: t("kpi.acceptanceRate"),
      value: `${acceptanceRate}%`,
      status:
        acceptanceRate > 60
          ? "positive"
          : acceptanceRate > 40
            ? "moderate"
            : "risk",
    },
    {
      label: t("kpi.aiUsageFrequency"),
      value: "42%",
      status: "moderate",
    },
    {
      label: t("kpi.motivation"),
      value: "3.95/5",
      status: "positive",
    },
    {
      label: t("kpi.dependencyRisk"),
      value: t("kpi.medium"),
      status: "moderate",
    },
    {
      label: t("kpi.correlation"),
      value: t("kpi.weak"),
      status: "moderate",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {kpis.map((kpi, index) => (
        <KpiCard
          key={index}
          label={kpi.label}
          value={kpi.value}
          status={kpi.status}
        />
      ))}
    </div>
  );
}
