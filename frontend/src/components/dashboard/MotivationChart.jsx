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
import { useTranslation } from "react-i18next";
import CustomTooltip from "../ui/CustomTooltip";

export default function MotivationChart({ data }) {
  const { isDark } = useTheme();
  const { t, i18n } = useTranslation();

  if (!data?.motivation_by_usage) {
    return (
      <div className="h-80 flex items-center justify-center text-gray-400 dark:text-gray-500">
        {t("common.noData")}
      </div>
    );
  }

  const chartData = Object.entries(data.motivation_by_usage)
    .sort(([leftKey], [rightKey]) =>
      leftKey.localeCompare(rightKey, undefined, { numeric: true }),
    )
    .map(([key, value]) => ({
      usageKey: key,
      motivation: value.avg_motivation || 0,
      count: value.count || 0,
    }));

  const textColor = isDark ? "#d1d5db" : "#6b7280";
  const gridColor = isDark ? "#374151" : "#e5e7eb";

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart
        key={i18n.language}
        data={chartData}
        margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
        <XAxis
          dataKey="usageKey"
          tickFormatter={(value) => t(`usageFrequency.${value}`)}
          style={{ fontSize: "12px", color: textColor }}
        />
        <YAxis style={{ fontSize: "12px", color: textColor }} domain={[0, 5]} />
        <Tooltip
          content={<CustomTooltip isDark={isDark} />}
          labelFormatter={(value) => t(`usageFrequency.${value}`)}
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
          name={t("charts.avgMotivation")}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
