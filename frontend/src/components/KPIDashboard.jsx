/**
 * Executive Analytics Dashboard
 *
 * Professional, corporate-style dashboard designed for executives and stakeholders.
 * Features real data visualizations and key performance metrics.
 */

import { useTranslation } from "react-i18next";
import ExecutiveKPICards from "./dashboard/ExecutiveKPICards";
import AcceptanceChart from "./dashboard/AcceptanceChart";
import MotivationChart from "./dashboard/MotivationChart";
import DepartmentChart from "./dashboard/DepartmentChart";
import DependencyChart from "./dashboard/DependencyChart";
import BenefitRiskBlock from "./dashboard/BenefitRiskBlock";
import CorrelationCard from "./dashboard/CorrelationCard";
import ChartCard from "./ui/ChartCard";
import SectionHeader from "./ui/SectionHeader";

export default function KPIDashboard({ data }) {
  const { t } = useTranslation();

  if (!data) {
    return (
      <div className="p-8 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <p className="text-gray-500 dark:text-gray-400">{t('dashboard.loading')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Executive KPI Cards - Top Summary */}
      <SectionHeader title={t('kpi.acceptanceRate')} />
      <ExecutiveKPICards data={data} />

      {/* Benefit vs Risk Executive Block */}
      <div className="mt-8">
        <SectionHeader title={t('benefitRisk.title')} />
        <BenefitRiskBlock data={data} />
      </div>

      {/* Charts Grid */}
      <div className="mt-8">
        <SectionHeader title="Detailed Analytics" description="In-depth performance metrics and trends" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <ChartCard title={t('charts.acceptanceDistribution')}>
            <AcceptanceChart data={data} />
          </ChartCard>
          <ChartCard title={t('charts.riskDistribution')}>
            <DependencyChart data={data} />
          </ChartCard>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <ChartCard title={t('charts.motivationTrend')}>
            <MotivationChart data={data} />
          </ChartCard>
          <ChartCard title={t('charts.departmentComparison')}>
            <DepartmentChart data={data} />
          </ChartCard>
        </div>
      </div>

      {/* Correlation Insight Card - Full Width */}
      <div className="mt-8">
        <ChartCard title={t('correlation.title')}>
          <CorrelationCard data={data} />
        </ChartCard>
      </div>
    </div>
  );
}
      <CorrelationCard data={data} />
    </div>
  );
}
