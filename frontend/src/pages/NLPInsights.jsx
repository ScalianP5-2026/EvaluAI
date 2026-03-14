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
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
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
  const [strategicSummary, setStrategicSummary] = useState(null);
  const hasStrategicSummary = Boolean(
    strategicSummary && strategicSummary.status !== "error",
  );

  const formatPercentageValue = (value, fractionDigits = 1) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return "—";
    }
    return `${Number(value).toFixed(fractionDigits)}%`;
  };

  const formatNumberValue = (value, fractionDigits = 2) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return "—";
    }
    return Number(value).toFixed(fractionDigits);
  };

  useEffect(() => {
    const loadNLPInsights = async () => {
      try {
        setLoading(true);
        setError(null);

        const [summaryResponse, strategicResponse] = await Promise.all([
          nlpAPI.getSummary(),
          nlpAPI.getStrategicSummary(),
        ]);

        const sentimentPayload = summaryResponse?.sentiment ?? {};
        const topicPayload = summaryResponse?.topic ?? {};
        const npiPayload = summaryResponse?.npi_distribution ?? {};

        const strategicStatus = strategicResponse?.status;

        const hasErrorStatus = [
          sentimentPayload,
          topicPayload,
          npiPayload,
        ].some((item) => item?.status === "error");

        if (hasErrorStatus || strategicStatus === "error") {
          const backendMessage =
            sentimentPayload?.message ||
            topicPayload?.message ||
            npiPayload?.message ||
            strategicResponse?.message;
          if (backendMessage) {
            setError({ type: "backend", message: backendMessage });
          } else {
            setError({ type: "translation", key: "nlp.errorLoading" });
          }
        }

        setSentiment(sentimentPayload);
        setTopic(topicPayload);
        setNpiDistribution(npiPayload);
        setStrategicSummary(
          strategicStatus === "error" ? null : (strategicResponse ?? null),
        );
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
        setStrategicSummary(null);
      } finally {
        setLoading(false);
      }
    };

    loadNLPInsights();
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadExecutiveSummary = async () => {
      try {
        const data = await nlpAPI.getExecutive(i18n.language || "en");
        if (!isMounted) return;

        const executiveText =
          data?.executive_summary ||
          data?.message ||
          t("nlp.executiveUnavailable");
        setExecutiveSummary(String(executiveText));
      } catch (execError) {
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
    };
  }, [i18n.language, t]);

  useEffect(() => {
    setLanguageKey(i18n.language);
  }, [i18n.language]);

  const translateSentimentLabel = (label) => t(`sentiment.${label}`) || label;
  const normalizeRiskKey = (label) => {
    if (!label) return "low";
    const normalized = String(label)
      .replace(/_risk$/i, "")
      .toLowerCase();
    if (normalized === "moderate") return "medium";
    return normalized;
  };
  const translateRiskLabel = (label) => {
    if (!label) return label;
    const normalized = normalizeRiskKey(label);
    return t(`risk.${normalized}`) || normalized || label;
  };
  const translateTopicLabel = (topicId) => {
    const numericId = Number(topicId);
    if (!Number.isNaN(numericId)) {
      return `${t("nlp.topic")} ${numericId + 1}`;
    }
    return `${t("nlp.topic")} ${topicId}`;
  };

  const sanitizeTopicId = (topicValue) => {
    if (topicValue === null || topicValue === undefined) {
      return "";
    }
    return String(topicValue)
      .replace(/^Topic\s+/i, "")
      .replace(/^#/, "");
  };

  const translateTopicDisplayName = (topicValue) => {
    if (!topicValue && topicValue !== 0) {
      return t("nlp.strategicKpis.noTopic");
    }
    return translateTopicLabel(sanitizeTopicId(topicValue));
  };

  const clampRatio = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return 0;
    }
    return Math.min(1, Math.max(0, Number(value)));
  };

  const getKpiToneClasses = (tone) => {
    const palette = {
      risk: isDark
        ? "border-rose-500/40 bg-rose-900/20 text-rose-100"
        : "border-rose-100 bg-rose-50 text-rose-900",
      signal: isDark
        ? "border-amber-500/40 bg-amber-900/20 text-amber-100"
        : "border-amber-100 bg-amber-50 text-amber-900",
      metric: isDark
        ? "border-emerald-500/40 bg-emerald-900/20 text-emerald-100"
        : "border-emerald-100 bg-emerald-50 text-emerald-900",
      topic: isDark
        ? "border-indigo-500/40 bg-indigo-900/20 text-indigo-100"
        : "border-indigo-100 bg-indigo-50 text-indigo-900",
    };
    return `rounded-2xl border px-5 py-4 shadow-sm ${palette[tone] || palette.metric}`;
  };

  const strategicKpiCards = useMemo(() => {
    if (!strategicSummary?.kpis) return [];

    const {
      high_ai_autonomy_dependency_risk_percent,
      neutral_sentiment_percent,
      avg_npi_score,
      top_risk_topic,
    } = strategicSummary.kpis;

    return [
      {
        key: "high_ai_autonomy_dependency_risk_percent",
        label: t("nlp.strategicKpis.highAiAutonomyDependencyRisk"),
        value: formatPercentageValue(
          high_ai_autonomy_dependency_risk_percent ?? null,
          1,
        ),
        caption: t("nlp.strategicKpis.highAiAutonomyDependencyRiskCaption"),
        tone: "risk",
      },
      {
        key: "neutral_sentiment_percent",
        label: t("nlp.strategicKpis.neutralSentiment"),
        value: formatPercentageValue(neutral_sentiment_percent ?? null, 1),
        caption: t("nlp.strategicKpis.neutralSentimentCaption"),
        tone: "signal",
      },
      {
        key: "avg_npi_score",
        label: t("nlp.strategicKpis.avgAiAutonomyDependencyScore"),
        value: formatNumberValue(avg_npi_score ?? null, 2),
        caption: t("nlp.strategicKpis.avgAiAutonomyDependencyScoreCaption"),
        tone: "metric",
      },
      {
        key: "top_risk_topic",
        label: t("nlp.strategicKpis.topRiskTopic"),
        value: translateTopicDisplayName(top_risk_topic),
        caption: t("nlp.strategicKpis.topRiskTopicCaption"),
        tone: "topic",
      },
    ];
  }, [strategicSummary, t, i18n.language]);

  const mlOverlapValue =
    strategicSummary?.ml_nlp_correlation?.dropout_high_and_npi_high_percent ??
    null;
  const mlOverlapDisplay = formatPercentageValue(mlOverlapValue ?? null, 1);
  const mlOverlapBarWidth = clampRatio((mlOverlapValue ?? 0) / 100) * 100;

  const radarChartData = useMemo(() => {
    if (!strategicSummary?.radar_metrics) return [];

    const metrics = strategicSummary.radar_metrics;
    return [
      {
        metric: t("nlp.radar.sentiment"),
        value: clampRatio(metrics.sentiment_positivity),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.autonomy"),
        value: clampRatio(metrics.autonomy_signal),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.dependency"),
        value: clampRatio(metrics.dependency_signal),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.motivation"),
        value: clampRatio(metrics.motivation_proxy),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.risk"),
        value: clampRatio(metrics.risk_level),
        fullMark: 1,
      },
    ];
  }, [strategicSummary, t, i18n.language]);

  const topTopicsRows = useMemo(() => {
    if (!strategicSummary?.top_topics_table) return [];
    return strategicSummary.top_topics_table.map((row) => ({
      ...row,
      topicLabel: translateTopicDisplayName(row.topic),
    }));
  }, [strategicSummary, i18n.language, t]);

  const strategicInsightText = useMemo(() => {
    if (!strategicSummary?.kpis) return "";
    const riskShare = formatPercentageValue(
      strategicSummary.kpis.high_ai_autonomy_dependency_risk_percent ?? null,
      1,
    );
    const overlapShare = formatPercentageValue(mlOverlapValue ?? null, 1);
    const avgScore = formatNumberValue(
      strategicSummary.kpis.avg_npi_score ?? null,
      2,
    );
    const topic = translateTopicDisplayName(
      strategicSummary.kpis.top_risk_topic,
    );

    return t("nlp.strategicInsight.body", {
      risk: riskShare,
      topic,
      overlap: overlapShare,
      npi: avgScore,
    });
  }, [strategicSummary, t, i18n.language, mlOverlapValue]);

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
  const radarReady = radarChartData.length > 0;
  const hasTopTopics = topTopicsRows.length > 0;
  const insightCopy = strategicInsightText || t("nlp.strategicInsight.default");

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

      {hasStrategicSummary && (
        <section className="space-y-6">
          <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-slate-900 dark:via-gray-900 dark:to-indigo-950 p-8 shadow-xl shadow-slate-100/40 dark:shadow-black/30">
            <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.35em] text-indigo-600 dark:text-indigo-300">
                  {t("nlp.strategicLayerBadge")}
                </p>
                <h2 className="text-2xl font-semibold text-slate-900 dark:text-white">
                  {t("nlp.strategicLayerTitle")}
                </h2>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  {t("nlp.strategicLayerSubtitle")}
                </p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
              {strategicKpiCards.map((card) => (
                <div key={card.key} className={getKpiToneClasses(card.tone)}>
                  <p className="text-xs font-semibold uppercase tracking-wide">
                    {card.label}
                  </p>
                  <p className="mt-2 text-3xl font-semibold">{card.value}</p>
                  <p className="mt-1 text-xs opacity-80">{card.caption}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {t("nlp.mlCorrelation.title")}
              </p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {t("nlp.mlCorrelation.subtitle")}
              </p>
              <div className="mt-6">
                <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-300">
                  <span>{t("nlp.mlCorrelation.overlapLabel")}</span>
                  <span>{mlOverlapDisplay}</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className="h-full rounded-full bg-indigo-500 dark:bg-indigo-400"
                    style={{ width: `${mlOverlapBarWidth}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg">
              <div className="flex flex-col gap-2">
                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                  {t("nlp.radar.title")}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {t("nlp.radar.description")}
                </p>
              </div>
              {!radarReady ? (
                <div className="h-64 flex items-center justify-center text-sm text-slate-400 dark:text-slate-500">
                  {t("nlp.noData")}
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarChartData} outerRadius="80%">
                    <PolarGrid stroke={isDark ? "#374151" : "#e5e7eb"} />
                    <PolarAngleAxis
                      dataKey="metric"
                      tick={{
                        fill: isDark ? "#e5e7eb" : "#475569",
                        fontSize: 12,
                      }}
                    />
                    <PolarRadiusAxis
                      tick={{ fill: isDark ? "#e5e7eb" : "#475569" }}
                      tickFormatter={(value) => `${Math.round(value * 100)}%`}
                      domain={[0, 1]}
                    />
                    <Radar
                      dataKey="value"
                      stroke="#6366f1"
                      fill="#6366f1"
                      fillOpacity={0.25}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {t("nlp.topTopics.title")}
              </p>
              {!hasTopTopics ? (
                <div className="mt-6 text-sm text-slate-500 dark:text-slate-400">
                  {t("nlp.topTopics.empty")}
                </div>
              ) : (
                <div className="mt-4 overflow-x-auto">
                  <table className="min-w-full text-sm">
                    <thead className="text-left text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      <tr>
                        <th className="py-2 pr-4 font-medium">
                          {t("nlp.topTopics.topic")}
                        </th>
                        <th className="py-2 pr-4 font-medium">
                          {t("nlp.topTopics.percent")}
                        </th>
                        <th className="py-2 pr-4 font-medium">
                          {t("nlp.topTopics.riskScore")}
                        </th>
                        <th className="py-2 pr-4 font-medium">
                          {t("nlp.topTopics.riskLevel")}
                        </th>
                        <th className="py-2 font-medium">
                          {t("nlp.topTopics.implication")}
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {topTopicsRows.map((row) => {
                        const implicationKey =
                          row.risk_level === "high"
                            ? "nlp.topTopics.implicationHigh"
                            : row.risk_level === "medium"
                              ? "nlp.topTopics.implicationMedium"
                              : "nlp.topTopics.implicationLow";
                        return (
                          <tr key={`${row.topic}-${row.percent}`}>
                            <td className="py-3 pr-4 text-slate-900 dark:text-slate-100">
                              {row.topicLabel}
                            </td>
                            <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                              {formatPercentageValue(row.percent ?? null, 1)}
                            </td>
                            <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                              {formatNumberValue(
                                row.avg_topic_risk_score ?? null,
                                2,
                              )}
                            </td>
                            <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                              {translateRiskLabel(row.risk_level || "low")}
                            </td>
                            <td className="py-3 text-slate-600 dark:text-slate-300">
                              {t(implicationKey)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {t("nlp.strategicInsight.title")}
              </p>
              <p className="mt-4 text-sm leading-7 text-slate-600 dark:text-slate-200 whitespace-pre-wrap">
                {insightCopy}
              </p>
            </div>
          </div>
        </section>
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
        <ChartCard title={t("nlp.aiAutonomyDependencyIndex")}>
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
            {t("nlp.aiAutonomyDependencyDescription")}
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
