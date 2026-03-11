/**
 * Acceptance Distribution Chart - Bar Chart
 *
 * Shows distribution of acceptance levels across respondents.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";

export default function AcceptanceChart({ data }) {
  const { isDark } = useTheme();

  if (!data?.acceptance_distribution) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 dark:text-gray-500">
        No data
      </div>
    );
  }

  const chartData = [
    {
      name: "Very Low",
      value: data.acceptance_distribution.very_low,
      fill: "#ef4444",
    },
    { name: "Low", value: data.acceptance_distribution.low, fill: "#f97316" },
    {
      name: "Medium",
      value: data.acceptance_distribution.medium,
      fill: "#eab308",
    },
    { name: "High", value: data.acceptance_distribution.high, fill: "#84cc16" },
    {
      name: "Very High",
      value: data.acceptance_distribution.very_high,
      fill: "#22c55e",
    },
  ];

  const textColor = isDark ? "#d1d5db" : "#6b7280";
  const gridColor = isDark ? "#374151" : "#e5e7eb";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart
        data={chartData}
        margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="name" style={{ fontSize: "12px", color: textColor }} />
        <YAxis style={{ fontSize: "12px", color: textColor }} />
        <Tooltip
          contentStyle={{
            backgroundColor: isDark ? "#1f2937" : "#ffffff",
            border: `1px solid ${gridColor}`,
            borderRadius: "8px",
            boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            color: textColor,
          }}
          formatter={(value) => `${value} responses`}
        />
        <Bar dataKey="value" radius={[8, 8, 0, 0]}>
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
