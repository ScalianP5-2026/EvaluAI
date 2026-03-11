/**
 * Department Segmentation Chart - Grouped Bar Chart
 * Compares motivation and autoeficacia (digital self-efficacy) across departments
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";

export default function DepartmentChart({ data }) {
  const { isDark } = useTheme();

  if (!data?.department_segmentation) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 dark:text-gray-500">
        No data
      </div>
    );
  }

  const chartData = Object.entries(data.department_segmentation).map(
    ([dept, metrics]) => ({
      name: dept,
      motivation: metrics.avg_motivation || 0,
      autoeficacia: metrics.avg_autoeficacia || 0,
      count: metrics.count || 0,
    }),
  );

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
          formatter={(value) => value.toFixed(2)}
        />
        <Legend />
        <Bar
          dataKey="motivation"
          fill="#3b82f6"
          radius={[8, 8, 0, 0]}
          name="Motivation"
        />
        <Bar
          dataKey="autoeficacia"
          fill="#8b5cf6"
          radius={[8, 8, 0, 0]}
          name="Digital Self-Efficacy"
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
