/**
 * Executive Analytics Dashboard
 *
 * Professional, corporate-style dashboard designed for executives and stakeholders.
 * Features real data visualizations and key performance metrics.
 */

import { useTranslation } from "react-i18next";
import ScalianBanner from "./ScalianBanner";
import ExecutiveSnapshot from "./ExecutiveSnapshot";
import ExecutiveSummary from "./ExecutiveSummary";
import AcceptanceChart from "./dashboard/AcceptanceChart";
import MotivationChart from "./dashboard/MotivationChart";
import DepartmentChart from "./dashboard/DepartmentChart";
import DependencyChart from "./dashboard/DependencyChart";
import CorrelationMetricsTable from "./dashboard/CorrelationMetricsTable";
import DatasetOverview from "./DatasetOverview";
import ExportSection from "./ExportSection";
import ChartCard from "./ui/ChartCard";

export default function KPIDashboard({ data }) {
  const { t } = useTranslation();

  if (!data) {
    return (
      <div className="p-8 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-gray-500 dark:text-gray-400">
          {t("dashboard.loading")}
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* SCALIAN Branding Banner */}
      <ScalianBanner />

      {/* Main Content */}
      <div className="px-8 py-8">
        {/* 1️⃣ EXECUTIVE SNAPSHOT */}
        <ExecutiveSnapshot data={data} />

        {/* 2️⃣ EXECUTIVE SUMMARY */}
        <ExecutiveSummary />

        {/* 3️⃣ BEHAVIORAL & ADOPTION ANALYTICS */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            {t("dashboard.analyticsTitle")}
          </h2>

          {/* Row 1: Acceptance + Motivation */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            <div id="chart-acceptance">
              <ChartCard
                title={t("charts.acceptanceDistribution")}
                subtitle={t("charts.acceptanceExplanation")}
              >
                <AcceptanceChart data={data} />
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.acceptanceInsight1")}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.acceptanceInsight2")}
                  </p>
                </div>
              </ChartCard>
            </div>

            <div id="chart-motivation">
              <ChartCard
                title={t("charts.motivationTrend")}
                subtitle={t("charts.motivationExplanation")}
              >
                <MotivationChart data={data} />
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.motivationInsight1")}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.motivationInsight2")}
                  </p>
                </div>
              </ChartCard>
            </div>
          </div>

          {/* Row 2: Department + Risk */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div id="chart-department">
              <ChartCard
                title={t("charts.departmentComparison")}
                subtitle={t("charts.departmentExplanation")}
              >
                <DepartmentChart data={data} />
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.departmentInsight1")}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.departmentInsight2")}
                  </p>
                </div>
              </ChartCard>
            </div>

            <div id="chart-dependency">
              <ChartCard
                title={t("charts.riskDistribution")}
                subtitle={t("charts.riskExplanation")}
              >
                <DependencyChart data={data} />
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.riskInsight1")}
                  </p>
                  <p className="text-xs text-gray-600 dark:text-gray-400">
                    {t("charts.riskInsight2")}
                  </p>
                </div>
              </ChartCard>
            </div>
          </div>
        </div>

        {/* 4️⃣ RISK & CORRELATION ANALYSIS */}
        <div className="mb-12">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {t("correlation.title")}
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
            {t("correlation.subtitle")}
          </p>

          <ChartCard>
            <CorrelationMetricsTable data={data} />
          </ChartCard>
        </div>

        {/* 5️⃣ DATASET OVERVIEW */}
        <DatasetOverview data={data} />

        {/* 6️⃣ EXPORT SECTION */}
        <ExportSection data={data} />
      </div>
    </div>
  );
}
