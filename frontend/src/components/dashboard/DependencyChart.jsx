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

export default function DependencyChart({ data }) {
  const { isDark } = useTheme();

  if (!data?.dependency_risk) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 dark:text-gray-500">
        No data
      </div>
    );
  }

  const chartData = [
    {
      name: "High Risk",
      value: data.dependency_risk.high_risk,
      fill: "#dc2626",
    },
    {
      name: "Medium Risk",
      value: data.dependency_risk.medium_risk,
      fill: "#f59e0b",
    },
    { name: "Low Risk", value: data.dependency_risk.low_risk, fill: "#10b981" },
  ];

  const gridColor = isDark ? "#374151" : "#e5e7eb";
  const textColor = isDark ? "#d1d5db" : "#6b7280";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, value }) => `${name}: ${value}`}
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
          formatter={(value) => `${value} respondents`}
          contentStyle={{
            backgroundColor: isDark ? "#1f2937" : "#ffffff",
            border: `1px solid ${gridColor}`,
            borderRadius: "8px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            color: textColor,
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
