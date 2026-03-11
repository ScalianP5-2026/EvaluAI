/**
 * Motivation by AI Usage Chart - Line Chart
 * Shows how motivation varies across different AI usage frequencies
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { useTheme } from "../../context/ThemeContext";

export default function MotivationChart({ data }) {
  const { isDark } = useTheme();

  if (!data?.motivation_by_usage) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 dark:text-gray-500">
        No data
      </div>
    );
  }

  const chartData = Object.entries(data.motivation_by_usage).map(
    ([key, value]) => ({
      name: key
        .replace(/_/g, " ")
        .split(" ")
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" "),
      motivation: value.avg_motivation || 0,
      count: value.count || 0,
    }),
  );

  const textColor = isDark ? "#d1d5db" : "#6b7280";
  const gridColor = isDark ? "#374151" : "#e5e7eb";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart
        data={chartData}
        margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis dataKey="name" style={{ fontSize: "12px", color: textColor }} />
        <YAxis style={{ fontSize: "12px", color: textColor }} domain={[0, 5]} />
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
        <Line
          type="monotone"
          dataKey="motivation"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={{ fill: "#3b82f6", r: 4 }}
          activeDot={{ r: 6 }}
          name="Avg Motivation"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
