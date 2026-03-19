/**
 * Dependency Risk Chart - Donut Chart
 * Shows risk distribution: High, Medium, Low dependency on AI
 */

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";
import { useTranslation } from "react-i18next";
import CustomTooltip from "../ui/CustomTooltip";

export default function DependencyChart({ data }) {
  const { isDark } = useTheme();
  const { t } = useTranslation();

  if (!data?.dependency_risk) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 dark:text-gray-500">
        {t("common.noData")}
      </div>
    );
  }

  const chartData = [
    {
      name: t("dataset.highRisk"),
      value: data.dependency_risk.high_risk,
      fill: "#dc2626",
    },
    {
      name: t("dataset.mediumRisk"),
      value: data.dependency_risk.medium_risk,
      fill: "#f59e0b",
    },
    {
      name: t("dataset.lowRisk"),
      value: data.dependency_risk.low_risk,
      fill: "#10b981",
    },
  ];

  const textColor = isDark ? "#d1d5db" : "#6b7280";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, value, x, y, textAnchor }) => (
            <text x={x} y={y} fill={textColor} textAnchor={textAnchor} fontSize={12}>
              {`${name}: ${value}`}
            </text>
          )}
          outerRadius={100}
          innerRadius={60}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value) => `${value} ${t("common.respondents")}`}
          content={<CustomTooltip isDark={isDark} />}
        />
        <Legend wrapperStyle={{ color: textColor }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
