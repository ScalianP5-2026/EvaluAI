import { useEffect, useMemo, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { nlpAPI } from "../services/api";
import SectionHeader from "../components/ui/SectionHeader";
import ChartCard from "../components/ui/ChartCard";
import { useTheme } from "../context/ThemeContext";
import CustomTooltip from "../components/ui/CustomTooltip";
import { useTranslation } from "react-i18next";

const NPI_COLORS = ["#10b981", "#f59e0b", "#ef4444", "#6b7280"];

export default function NLPInsights() {
  const { t, i18n } = useTranslation();
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [languageKey, setLanguageKey] = useState(i18n.language);

  const [sentiment, setSentiment] = useState({});
  const [topic, setTopic] = useState({});
  const [npiDistribution, setNpiDistribution] = useState({});
  const [executiveSummary, setExecutiveSummary] = useState("");

  useEffect(() => {
    const loadNLPInsights = async () => {
      try {
        setLoading(true);
        setError(null);

        const summaryResponse = await nlpAPI.getSummary();

        console.log("NLP summary response:", summaryResponse);

        // Read summary payload safely and provide fallback empty objects.
        const sentimentPayload = summaryResponse?.sentiment ?? {};
        const topicPayload = summaryResponse?.topic ?? {};
        const npiPayload = summaryResponse?.npi_distribution ?? {};

        // If backend service reports error status, keep UI alive with fallback message.
        const hasErrorStatus = [
          sentimentPayload,
          topicPayload,
          npiPayload,
        ].some((item) => item?.status === "error");

        if (hasErrorStatus) {
          const backendMessage =
            sentimentPayload?.message ||
            topicPayload?.message ||
            npiPayload?.message;
          if (backendMessage) {
            setError({ type: "backend", message: backendMessage });
          } else {
            setError({ type: "translation", key: "nlp.errorLoading" });
          }
        }

        setSentiment(sentimentPayload);
        setTopic(topicPayload);
        setNpiDistribution(npiPayload);
      } catch (requestError) {
        console.error("NLP insights request error:", requestError);
        const backendMessage =
          requestError?.response?.data?.message ||
          requestError?.response?.data?.detail;
        if (backendMessage) {
          setError({ type: "backend", message: backendMessage });
        } else {
          setError({ type: "translation", key: "nlp.errorLoading" });
        }
      } finally {
        setLoading(false);
      }
    };

    loadNLPInsights();
  }, []);

  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();
    const langParam = encodeURIComponent(i18n.language || "en");

    const loadExecutiveSummary = async () => {
      try {
        const response = await fetch(`/api/nlp/executive?lang=${langParam}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Executive summary request failed (${response.status})`,
          );
        }

        const data = await response.json();
        if (!isMounted) return;

        const executiveText =
          data?.executive_summary ||
          data?.message ||
          t("nlp.executiveUnavailable");
        setExecutiveSummary(String(executiveText));
      } catch (execError) {
        if (controller.signal.aborted) {
          return;
        }
        console.error("NLP executive summary request error:", execError);
        if (isMounted) {
          setExecutiveSummary("");
        }
      }
    };

    setExecutiveSummary("");
    loadExecutiveSummary();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [i18n.language, t]);

  useEffect(() => {
    setLanguageKey(i18n.language);
  }, [i18n.language]);

  const translateSentimentLabel = (label) => t(`sentiment.${label}`) || label;
  const translateRiskLabel = (label) => {
    if (!label) return label;
    const normalized = label.replace(/_risk$/i, "");
    return t(`risk.${normalized}`) || t(`risk.${label}`) || normalized || label;
  };
  const translateTopicLabel = (topicId) => {
    const numericId = Number(topicId);
    if (!Number.isNaN(numericId)) {
      return `${t("nlp.topic")} ${numericId + 1}`;
    }
    return `${t("nlp.topic")} ${topicId}`;
  };

  const sentimentChartData = useMemo(() => {
    if (!sentiment?.sentiment_percentages) return [];

    return Object.entries(sentiment.sentiment_percentages).map(
      ([label, value]) => ({
        label: translateSentimentLabel(label),
        value: Number(value || 0),
      }),
    );
  }, [sentiment, i18n.language]);

  const topicChartData = useMemo(() => {
    if (!topic?.top_10_topics) return [];

    return Object.entries(topic.top_10_topics).map(([topicId, count]) => ({
      topic: translateTopicLabel(topicId),
      count: Number(count || 0),
    }));
  }, [topic, i18n.language]);

  const npiChartData = useMemo(() => {
    if (!npiDistribution?.npi_category_percentages) return [];

    return Object.entries(npiDistribution.npi_category_percentages).map(
      ([label, value]) => ({
        label: translateRiskLabel(label),
        value: Number(value || 0),
      }),
    );
  }, [npiDistribution, i18n.language]);

  const sentimentReady =
    sentiment?.status === "ok" &&
    sentiment?.sentiment_percentages &&
    Object.keys(sentiment.sentiment_percentages).length > 0;

  const topicReady =
    topic?.status === "ok" &&
    topic?.top_10_topics &&
    Object.keys(topic.top_10_topics).length > 0;

  const npiReady =
    npiDistribution?.status === "ok" &&
    npiDistribution?.npi_category_percentages &&
    Object.keys(npiDistribution.npi_category_percentages).length > 0;

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-pulse text-gray-500 dark:text-gray-400">
          {t("nlp.loading")}
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      <SectionHeader title={t("nlp.title")} description={t("nlp.subtitle")} />

      {error && (
        <div className="bg-amber-50 dark:bg-amber-900 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-100 rounded-lg p-4">
          {error.type === "translation" ? t(error.key) : error.message}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <ChartCard title={t("nlp.sentimentOverview")}>
          {!sentimentReady || sentimentChartData.length === 0 ? (
            <div className="h-72 flex items-center justify-center text-gray-400 dark:text-gray-500">
              {t("nlp.noData")}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart key={languageKey} data={sentimentChartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={isDark ? "#374151" : "#e5e7eb"}
                />
                <XAxis
                  dataKey="label"
                  tick={{ fill: isDark ? "#d1d5db" : "#6b7280" }}
                />
                <YAxis
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                  tick={{ fill: isDark ? "#d1d5db" : "#6b7280" }}
                />
                <Tooltip
                  content={<CustomTooltip isDark={isDark} />}
                  formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`}
                />
                <Bar dataKey="value" fill="#2563eb" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
          <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
            {t("nlp.sentimentDescription")}
          </p>
        </ChartCard>

        <ChartCard title={t("nlp.topicDistribution")}>
          {!topicReady || topicChartData.length === 0 ? (
            <div className="h-72 flex items-center justify-center text-gray-400 dark:text-gray-500">
              {t("nlp.noData")}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart key={languageKey} data={topicChartData}>
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke={isDark ? "#374151" : "#e5e7eb"}
                />
                <XAxis
                  dataKey="topic"
                  tick={{ fill: isDark ? "#d1d5db" : "#6b7280" }}
                  interval={0}
                  angle={-20}
                  textAnchor="end"
                  height={64}
                />
                <YAxis tick={{ fill: isDark ? "#d1d5db" : "#6b7280" }} />
                <Tooltip content={<CustomTooltip isDark={isDark} />} />
                <Bar dataKey="count" fill="#0ea5e9" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
          <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
            {t("nlp.topicDescription")}
          </p>
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <ChartCard title={t("nlp.psychologicalIndex")}>
          {!npiReady || npiChartData.length === 0 ? (
            <div className="h-72 flex items-center justify-center text-gray-400 dark:text-gray-500">
              {t("nlp.noData")}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart key={languageKey}>
                <Pie
                  data={npiChartData}
                  dataKey="value"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  innerRadius={65}
                  outerRadius={100}
                  label={({ label, value }) =>
                    `${label}: ${(Number(value) * 100).toFixed(1)}%`
                  }
                >
                  {npiChartData.map((entry, index) => (
                    <Cell
                      key={`npi-cell-${entry.name}`}
                      fill={NPI_COLORS[index % NPI_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={<CustomTooltip isDark={isDark} />}
                  formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
          <p className="chart-description mt-4 text-sm text-gray-500 dark:text-gray-400">
            {t("nlp.psychologicalDescription")}
          </p>
        </ChartCard>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
            {t("nlp.executiveInsight")}
          </h2>
          <div className="min-h-[300px] rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-5">
            <p className="text-sm leading-7 text-gray-700 dark:text-gray-200 whitespace-pre-wrap">
              {executiveSummary || t("nlp.executiveUnavailable")}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
