import { useEffect, useMemo, useState, useCallback } from "react";
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
import { useAuth } from "../context/AuthContext";

const NPI_COLORS = ["#10b981", "#f59e0b", "#ef4444", "#6b7280"];
const SEVERITY_COLORS = {
  high: {
    bg: "bg-rose-50 dark:bg-rose-900/30",
    border: "border-rose-200 dark:border-rose-700",
    text: "text-rose-800 dark:text-rose-200",
  },
  medium: {
    bg: "bg-amber-50 dark:bg-amber-900/30",
    border: "border-amber-200 dark:border-amber-700",
    text: "text-amber-800 dark:text-amber-200",
  },
  low: {
    bg: "bg-sky-50 dark:bg-sky-900/30",
    border: "border-sky-200 dark:border-sky-700",
    text: "text-sky-800 dark:text-sky-200",
  },
};

const TABS = {
  overview: "overview",
  topics: "topics",
  alerts: "alerts",
  profile: "profile",
};

function TabButton({ active, onClick, children, badge }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200 whitespace-nowrap ${
        active
          ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/30"
          : "text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
      }`}
    >
      {children}
      {badge > 0 && (
        <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] rounded-full bg-rose-500 text-white text-[10px] font-bold flex items-center justify-center px-1">
          {badge}
        </span>
      )}
    </button>
  );
}

export default function NLPInsights() {
  const { t, i18n } = useTranslation();
  const { isDark } = useTheme();
  const { isRRHH, user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(
    isRRHH ? TABS.overview : TABS.profile,
  );
  const [languageKey, setLanguageKey] = useState(i18n.language);

  const [sentiment, setSentiment] = useState({});
  const [topic, setTopic] = useState({});
  const [npiDistribution, setNpiDistribution] = useState({});
  const [executiveSummary, setExecutiveSummary] = useState("");
  const [strategicSummary, setStrategicSummary] = useState(null);
  const [alertsData, setAlertsData] = useState(null);
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

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

  const translateSentimentLabel = (label) => t(`sentiment.${label}`) || label;

  const normalizeRiskKey = (label) => {
    if (!label) return "low";
    const normalized = String(label)
      .replace(/_risk$/i, "")
      .toLowerCase();
    return normalized === "moderate" ? "medium" : normalized;
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

    const topicNames = {
      tools_and_platforms:
        i18n.language === "es"
          ? "Herramientas y plataformas"
          : "Tools & Platforms",
      learning_experience:
        i18n.language === "es"
          ? "Experiencia de aprendizaje"
          : "Learning Experience",
      time_and_workload:
        i18n.language === "es" ? "Tiempo y carga" : "Time & Workload",
      motivation_and_engagement:
        i18n.language === "es"
          ? "Motivación y compromiso"
          : "Motivation & Engagement",
      difficulty_and_barriers:
        i18n.language === "es"
          ? "Dificultades y barreras"
          : "Difficulty & Barriers",
      mentoring_and_support:
        i18n.language === "es" ? "Mentoría y apoyo" : "Mentoring & Support",
      autonomy_and_dependency:
        i18n.language === "es"
          ? "Autonomía y dependencia"
          : "Autonomy & Dependency",
      impact_and_value:
        i18n.language === "es" ? "Impacto y valor" : "Impact & Value",
      no_topic:
        i18n.language === "es" ? "Sin tema dominante" : "No dominant topic",
    };

    return topicNames[topicId] || topicId;
  };

  const sanitizeTopicId = (topicValue) => {
    if (topicValue === null || topicValue === undefined) return "";
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
    return `rounded-2xl border px-5 py-4 shadow-sm ${
      palette[tone] || palette.metric
    }`;
  };

  const alertLabelMap = {
    high_dependency:
      i18n.language === "es" ? "Alta dependencia IA" : "High AI Dependency",
    negative_sentiment:
      i18n.language === "es" ? "Sentimiento negativo" : "Negative Sentiment",
    difficulty_barriers:
      i18n.language === "es"
        ? "Dificultades y barreras"
        : "Difficulty & Barriers",
    low_motivation:
      i18n.language === "es" ? "Baja motivación" : "Low Motivation",
    time_pressure:
      i18n.language === "es" ? "Presión de tiempo" : "Time Pressure",
    mentoring_needs:
      i18n.language === "es" ? "Necesita mentoría" : "Mentoring Needs",
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        const promises = [nlpAPI.getSummary(), nlpAPI.getStrategicSummary()];
        if (isRRHH) promises.push(nlpAPI.getAlerts());

        const results = await Promise.all(promises);
        const [summaryResponse, strategicResponse, alertsResponse] = results;

        setSentiment(summaryResponse?.sentiment ?? {});
        setTopic(summaryResponse?.topic ?? {});
        setNpiDistribution(summaryResponse?.npi_distribution ?? {});

        const strategicStatus = strategicResponse?.status;
        setStrategicSummary(
          strategicStatus === "error" ? null : (strategicResponse ?? null),
        );

        if (alertsResponse && alertsResponse.status === "ok") {
          setAlertsData(alertsResponse);
        }

        const hasErrorStatus = [
          summaryResponse?.sentiment,
          summaryResponse?.topic,
          summaryResponse?.npi_distribution,
        ].some((item) => item?.status === "error");

        if (hasErrorStatus || strategicStatus === "error") {
          const msg =
            summaryResponse?.sentiment?.message ||
            summaryResponse?.topic?.message ||
            strategicResponse?.message;

          setError(
            msg
              ? { type: "backend", message: msg }
              : { type: "translation", key: "nlp.errorLoading" },
          );
        }
      } catch (requestError) {
        console.error("NLP insights request error:", requestError);
        const msg =
          requestError?.response?.data?.message ||
          requestError?.response?.data?.detail;

        setError(
          msg
            ? { type: "backend", message: msg }
            : { type: "translation", key: "nlp.errorLoading" },
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [isRRHH]);

  useEffect(() => {
    let isMounted = true;

    const loadExec = async () => {
      try {
        const data = await nlpAPI.getExecutive(i18n.language || "en");
        if (!isMounted) return;
        setExecutiveSummary(
          String(
            data?.executive_summary ||
              data?.message ||
              t("nlp.executiveUnavailable"),
          ),
        );
      } catch {
        if (isMounted) setExecutiveSummary("");
      }
    };

    setExecutiveSummary("");
    loadExec();

    return () => {
      isMounted = false;
    };
  }, [i18n.language, t]);

  const loadEmployeeProfile = useCallback(async () => {
    if (!user) return;

    const employeeId =
      user.id_empleado || user.employee_id || user.id || user.email;

    setProfileLoading(true);

    try {
      const data = await nlpAPI.getEmployee(employeeId);

      setEmployeeProfile(data?.status === "ok" ? data.employee : null);
    } catch (err) {
      console.error("NLP employee profile error:", err);
      setEmployeeProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (activeTab === TABS.profile) {
      loadEmployeeProfile();
    }
  }, [activeTab, loadEmployeeProfile]);

  useEffect(() => {
    setLanguageKey(i18n.language);
  }, [i18n.language]);

  const strategicKpiCards = useMemo(() => {
    if (!strategicSummary?.kpis) return [];

    const {
      high_ai_autonomy_dependency_risk_percent,
      positive_sentiment_percent,
      negative_sentiment_percent,
      avg_npi_score,
      top_risk_topic,
    } = strategicSummary.kpis;

    return [
      {
        key: "risk",
        label: t("nlp.strategicKpis.highAiAutonomyDependencyRisk"),
        value: formatPercentageValue(
          high_ai_autonomy_dependency_risk_percent ?? null,
          1,
        ),
        caption: t("nlp.strategicKpis.highAiAutonomyDependencyRiskCaption"),
        tone: "risk",
      },
      {
        key: "positive",
        label: t("nlp.strategicKpis.positiveSentiment"),
        value: formatPercentageValue(positive_sentiment_percent ?? null, 1),
        caption: t("nlp.strategicKpis.positiveSentimentCaption"),
        tone: "metric",
      },
      {
        key: "negative",
        label: t("nlp.strategicKpis.negativeSentiment"),
        value: formatPercentageValue(negative_sentiment_percent ?? null, 1),
        caption: t("nlp.strategicKpis.negativeSentimentCaption"),
        tone: "risk",
      },
      {
        key: "npi",
        label: t("nlp.strategicKpis.avgAiAutonomyDependencyScore"),
        value: formatPercentageValue((avg_npi_score ?? 0) * 100, 1),
        caption: t("nlp.strategicKpis.avgAiAutonomyDependencyScoreCaption"),
        tone: "metric",
      },
      {
        key: "topic",
        label: t("nlp.strategicKpis.topRiskTopic"),
        value: translateTopicDisplayName(top_risk_topic),
        caption: t("nlp.strategicKpis.topRiskTopicCaption"),
        tone: "topic",
      },
    ];
  }, [strategicSummary, t, i18n.language]);

  const radarChartData = useMemo(() => {
    if (!strategicSummary?.radar_metrics) return [];

    const m = strategicSummary.radar_metrics;
    return [
      {
        metric: t("nlp.radar.sentiment"),
        value: clampRatio(m.sentiment_positivity),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.autonomy"),
        value: clampRatio(m.autonomy_signal),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.dependency"),
        value: clampRatio(m.dependency_signal),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.motivation"),
        value: clampRatio(m.motivation_proxy),
        fullMark: 1,
      },
      {
        metric: t("nlp.radar.risk"),
        value: clampRatio(m.risk_level),
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

  const mlOverlapValue =
    strategicSummary?.ml_nlp_correlation?.dropout_high_and_npi_high_percent ??
    null;
  const mlOverlapDisplay = formatPercentageValue(mlOverlapValue, 1);
  const mlOverlapBarWidth = clampRatio((mlOverlapValue ?? 0) / 100) * 100;

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

  const alertCount =
    alertsData?.alert_panels?.reduce((sum, p) => sum + (p.count || 0), 0) || 0;

  if (loading) {
    return (
      <div className="p-8 text-center">
        <div className="animate-pulse text-gray-500 dark:text-gray-400">
          {t("nlp.loading")}
        </div>
      </div>
    );
  }

  const renderOverview = () => (
    <div className="space-y-8">
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

            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
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
                {mlOverlapValue === 0 || mlOverlapValue === null ? (
                  <div className="flex items-center gap-2 rounded-xl bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 p-4">
                    <span className="text-emerald-600 dark:text-emerald-400 text-lg">
                      ✅
                    </span>
                    <p className="text-sm text-emerald-800 dark:text-emerald-200">
                      {t("nlp.mlCorrelation.noOverlapMessage")}
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between text-xs font-semibold text-slate-500 dark:text-slate-300">
                      <span>{t("nlp.mlCorrelation.overlapLabel")}</span>
                      <span>{mlOverlapDisplay}</span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-800">
                      <div
                        className="h-full rounded-full bg-indigo-500 dark:bg-indigo-400"
                        style={{ width: `${mlOverlapBarWidth}%` }}
                      />q
                  </>
                )}
              </div>
            </div>

            <div className="xl:col-span-2 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg">
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                {t("nlp.radar.title")}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {t("nlp.radar.description")}
              </p>
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
                      tickFormatter={(v) => `${Math.round(v * 100)}%`}
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
        </section>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        <ChartCard title={t("nlp.sentimentChartTitle")}>
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
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                  tick={{ fill: isDark ? "#d1d5db" : "#6b7280" }}
                />
                <Tooltip
                  content={<CustomTooltip isDark={isDark} />}
                  formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`}
                />
                <Bar dataKey="value" fill="#2563eb" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

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
                      key={`npi-${index}`}
                      fill={NPI_COLORS[index % NPI_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={<CustomTooltip isDark={isDark} />}
                  formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
          {t("nlp.executiveInsight")}
        </h2>
        <div className="min-h-[200px] rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-5">
          <p className="text-sm leading-7 text-gray-700 dark:text-gray-200 whitespace-pre-wrap">
            {executiveSummary || t("nlp.executiveUnavailable")}
          </p>
        </div>
      </div>
    </div>
  );

  const renderTopics = () => (
    <div className="space-y-8">
      <ChartCard
        title={
          i18n.language === "es"
            ? "Distribución de Temas"
            : "Topic Distribution"
        }
      >
        {!topicReady || topicChartData.length === 0 ? (
          <div className="h-72 flex items-center justify-center text-gray-400 dark:text-gray-500">
            {t("nlp.noData")}
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={350}>
            <BarChart
              key={languageKey}
              data={topicChartData}
              layout="vertical"
              margin={{ left: 20 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={isDark ? "#374151" : "#e5e7eb"}
              />
              <XAxis
                type="number"
                tick={{ fill: isDark ? "#d1d5db" : "#6b7280" }}
              />
              <YAxis
                type="category"
                dataKey="topic"
                tick={{
                  fill: isDark ? "#d1d5db" : "#6b7280",
                  fontSize: 12,
                }}
                width={180}
              />
              <Tooltip content={<CustomTooltip isDark={isDark} />} />
              <Bar dataKey="count" fill="#0ea5e9" radius={[0, 6, 6, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      {hasTopTopics && (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg">
          <p className="text-sm font-semibold text-slate-900 dark:text-white mb-4">
            {t("nlp.topTopics.title")}
          </p>
          <div className="overflow-x-auto">
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
                        {formatNumberValue(row.avg_topic_risk_score ?? null, 2)}
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
        </div>
      )}
    </div>
  );

  const renderAlerts = () => {
    if (!alertsData) {
      return (
        <div className="h-48 flex items-center justify-center text-gray-400 dark:text-gray-500">
          {t("nlp.noData")}
        </div>
      );
    }

    const {
      alert_panels = [],
      department_cohorts = [],
      intervention_priorities = [],
      wave_breakdown = [],
    } = alertsData;

    return (
      <div className="space-y-8">
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
              alertsData.data_source === "db"
                ? "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300"
                : "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300"
            }`}
          >
            {alertsData.data_source === "db" ? "🟢 Live DB" : "📄 CSV Fallback"}
          </span>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {alertsData.total_responses}{" "}
            {i18n.language === "es" ? "respuestas" : "responses"}
          </span>
        </div>

        <section>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
            {i18n.language === "es" ? "Alertas Activas" : "Active Alerts"}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {alert_panels.map((panel) => {
              const severity =
                SEVERITY_COLORS[panel.severity] || SEVERITY_COLORS.low;

              return (
                <div
                  key={panel.alert_key}
                  className={`rounded-2xl border p-5 ${severity.bg} ${severity.border} shadow-sm transition-all duration-200 hover:shadow-md`}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">{panel.icon}</span>
                    <div>
                      <p className={`text-sm font-semibold ${severity.text}`}>
                        {alertLabelMap[panel.alert_key] || panel.label}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {panel.severity.toUpperCase()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-baseline gap-2">
                    <span className={`text-3xl font-bold ${severity.text}`}>
                      {panel.count}
                    </span>
                    <span className="text-sm text-slate-500 dark:text-slate-400">
                      ({formatPercentageValue(panel.percent, 1)})
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {department_cohorts.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              {i18n.language === "es"
                ? "Cohortes por Departamento"
                : "Department Cohorts"}
            </h3>
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Departamento" : "Department"}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Respuestas" : "Responses"}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es"
                        ? "Sent. Negativo"
                        : "Neg. Sentiment"}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Alta Dep." : "High Dep."}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Riesgo Medio" : "Avg Risk"}
                    </th>
                    <th className="py-2 font-medium">
                      {i18n.language === "es" ? "Motivación" : "Motivation"}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {department_cohorts.map((dept) => (
                    <tr key={dept.department}>
                      <td className="py-3 pr-4 font-medium text-slate-900 dark:text-slate-100">
                        {dept.department}
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                        {dept.count}
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                        {dept.negative_sentiment_count}
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                        {dept.high_dependency_count}
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                        {formatNumberValue(dept.avg_risk_score, 3)}
                      </td>
                      <td className="py-3 text-slate-600 dark:text-slate-300">
                        {formatNumberValue(dept.avg_motivation, 3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {intervention_priorities.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              {i18n.language === "es"
                ? "Prioridades de Intervención"
                : "Intervention Priorities"}
            </h3>
            <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-6 shadow-lg overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  <tr>
                    <th className="py-2 pr-4 font-medium">ID</th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Dept." : "Dept."}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Sentimiento" : "Sentiment"}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Tema" : "Topic"}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Riesgo" : "Risk"}
                    </th>
                    <th className="py-2 pr-4 font-medium">
                      {i18n.language === "es" ? "Dep." : "Dep."}
                    </th>
                    <th className="py-2 font-medium">
                      {i18n.language === "es" ? "Alertas" : "Alerts"}
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {intervention_priorities.map((emp, idx) => (
                    <tr key={`${emp.employee_id}-${idx}`}>
                      <td className="py-3 pr-4 font-mono text-xs text-slate-900 dark:text-slate-100">
                        {String(emp.employee_id).slice(0, 8)}
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                        {emp.department || "—"}
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                            emp.sentiment_label === "negative"
                              ? "bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300"
                              : emp.sentiment_label === "positive"
                                ? "bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-300"
                                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                          }`}
                        >
                          {translateSentimentLabel(emp.sentiment_label)}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300 text-xs">
                        {translateTopicLabel(emp.topic_id)}
                      </td>
                      <td className="py-3 pr-4 font-mono text-sm text-slate-900 dark:text-slate-100">
                        {formatNumberValue(emp.risk_score, 2)}
                      </td>
                      <td className="py-3 pr-4 text-slate-600 dark:text-slate-300">
                        {translateRiskLabel(emp.dependency_category)}
                      </td>
                      <td className="py-3">
                        <div className="flex flex-wrap gap-1">
                          {(emp.alert_flags || []).map((flag) => (
                            <span
                              key={flag}
                              className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-300"
                            >
                              {alertLabelMap[flag] || flag}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {wave_breakdown.length > 0 && (
          <section>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              {i18n.language === "es"
                ? "Desglose por Oleada"
                : "Wave Breakdown"}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {wave_breakdown.map((w) => (
                <div
                  key={w.wave}
                  className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-5 shadow-sm"
                >
                  <p className="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    {i18n.language === "es" ? "Oleada" : "Wave"}
                  </p>
                  <p className="text-xl font-semibold text-slate-900 dark:text-white mt-1">
                    {w.wave}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-sm">
                    <span className="text-slate-500 dark:text-slate-400">
                      {w.count}{" "}
                      {i18n.language === "es" ? "respuestas" : "responses"}
                    </span>
                    <span className="font-medium text-emerald-600 dark:text-emerald-400">
                      {formatPercentageValue(w.positive_sentiment_percent, 1)}{" "}
                      {i18n.language === "es" ? "positivo" : "positive"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    );
  };

  const renderProfile = () => {
    if (profileLoading) {
      return (
        <div className="h-48 flex items-center justify-center text-gray-400 dark:text-gray-500 animate-pulse">
          {t("nlp.loading")}
        </div>
      );
    }

    if (!employeeProfile) {
      return (
        <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-8 shadow-lg text-center">
          <p className="text-lg text-slate-500 dark:text-slate-400">
            {i18n.language === "es"
              ? "No se encontró perfil NLP para tu usuario."
              : "No NLP profile found for your account."}
          </p>
          <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
            {i18n.language === "es"
              ? "Completa una encuesta para generar tu perfil."
              : "Complete a survey to generate your profile."}
          </p>
        </div>
      );
    }

    const p = employeeProfile;
    const sentimentColor =
      p.sentiment_label === "positive"
        ? "text-emerald-600 dark:text-emerald-400"
        : p.sentiment_label === "negative"
          ? "text-rose-600 dark:text-rose-400"
          : "text-slate-600 dark:text-slate-400";

    return (
      <div className="space-y-6">
        <div className="rounded-3xl border border-slate-200 dark:border-slate-800 bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950 dark:to-gray-900 p-8 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div>
              <h3 className="text-2xl font-semibold text-slate-900 dark:text-white">
                {i18n.language === "es" ? "Mi Perfil NLP" : "My NLP Profile"}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {user?.email || ""}
              </p>
              {p.departamento && (
                <p className="text-sm text-indigo-600 dark:text-indigo-300 mt-1">
                  {p.departamento}
                </p>
              )}
            </div>

            <div className="flex flex-wrap gap-3">
              <div
                className={`rounded-xl border px-4 py-3 ${getKpiToneClasses(
                  "metric",
                )}`}
              >
                <p className="text-xs font-semibold uppercase">
                  {i18n.language === "es" ? "Sentimiento" : "Sentiment"}
                </p>
                <p className={`text-xl font-bold mt-1 ${sentimentColor}`}>
                  {translateSentimentLabel(p.sentiment_label)}
                </p>
              </div>

              <div
                className={`rounded-xl border px-4 py-3 ${getKpiToneClasses(
                  "risk",
                )}`}
              >
                <p className="text-xs font-semibold uppercase">
                  {i18n.language === "es" ? "Riesgo" : "Risk"}
                </p>
                <p className="text-xl font-bold mt-1">
                  {formatNumberValue(p.topic_risk_score, 2)}
                </p>
              </div>

              <div
                className={`rounded-xl border px-4 py-3 ${getKpiToneClasses(
                  "topic",
                )}`}
              >
                <p className="text-xs font-semibold uppercase">
                  {i18n.language === "es" ? "Tema" : "Topic"}
                </p>
                <p className="text-lg font-semibold mt-1">
                  {translateTopicLabel(p.topic_id)}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            {
              label:
                i18n.language === "es"
                  ? "Puntuación Sentimiento"
                  : "Sentiment Score",
              value: formatNumberValue(p.sentiment_score, 3),
            },
            {
              label: i18n.language === "es" ? "Confianza" : "Confidence",
              value: formatNumberValue(p.sentiment_confidence, 3),
            },
            {
              label:
                i18n.language === "es"
                  ? "Índice Dependencia"
                  : "Dependency Index",
              value: formatNumberValue(p.ai_autonomy_dependency_index, 3),
            },
            {
              label: i18n.language === "es" ? "Motivación" : "Motivation",
              value: formatNumberValue(p.motivation_proxy, 3),
            },
          ].map((m) => (
            <div
              key={m.label}
              className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 p-4 shadow-sm"
            >
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {m.label}
              </p>
              <p className="text-2xl font-semibold text-slate-900 dark:text-white mt-1">
                {m.value}
              </p>
            </div>
          ))}
        </div>

        {p.recommendations && p.recommendations.length > 0 && (
          <div className="rounded-2xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50 dark:bg-indigo-900/30 p-6 shadow-sm">
            <h4 className="text-sm font-semibold text-indigo-800 dark:text-indigo-200 uppercase tracking-wider mb-3">
              {i18n.language === "es" ? "Recomendaciones" : "Recommendations"}
            </h4>
            <ul className="space-y-2">
              {p.recommendations.map((rec, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 text-sm text-indigo-700 dark:text-indigo-300"
                >
                  <span className="text-indigo-500 dark:text-indigo-400 mt-0.5">
                    →
                  </span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {p.alert_flags && p.alert_flags.length > 0 && (
          <div className="rounded-2xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/30 p-6 shadow-sm">
            <h4 className="text-sm font-semibold text-amber-800 dark:text-amber-200 uppercase tracking-wider mb-3">
              {i18n.language === "es" ? "Alertas Activas" : "Active Alerts"}
            </h4>
            <div className="flex flex-wrap gap-2">
              {p.alert_flags.map((flag) => (
                <span
                  key={flag}
                  className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-amber-100 dark:bg-amber-900/50 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-700"
                >
                  {alertLabelMap[flag] || flag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      <SectionHeader
        title={t("nlp.title")}
        description={
          i18n.language === "es"
            ? "Analítica NLP de encuestas de formación"
            : "NLP analytics from training surveys"
        }
      />

      {error && (
        <div className="bg-amber-50 dark:bg-amber-900 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-100 rounded-lg p-4">
          {error.type === "translation" ? t(error.key) : error.message}
        </div>
      )}

      <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800/60 rounded-2xl p-1.5 overflow-x-auto">
        {isRRHH && (
          <>
            <TabButton
              active={activeTab === TABS.overview}
              onClick={() => setActiveTab(TABS.overview)}
            >
              {i18n.language === "es" ? "Visión General" : "Overview"}
            </TabButton>

            <TabButton
              active={activeTab === TABS.topics}
              onClick={() => setActiveTab(TABS.topics)}
            >
              {i18n.language === "es" ? "Temas" : "Topics"}
            </TabButton>

            <TabButton
              active={activeTab === TABS.alerts}
              onClick={() => setActiveTab(TABS.alerts)}
              badge={alertCount}
            >
              {i18n.language === "es" ? "Alertas" : "Alerts"}
            </TabButton>
          </>
        )}

        <TabButton
          active={activeTab === TABS.profile}
          onClick={() => setActiveTab(TABS.profile)}
        >
          {i18n.language === "es" ? "Mi Perfil" : "My Profile"}
        </TabButton>
      </div>

      <div className="min-h-[400px]">
        {activeTab === TABS.overview && isRRHH && renderOverview()}
        {activeTab === TABS.topics && isRRHH && renderTopics()}
        {activeTab === TABS.alerts && isRRHH && renderAlerts()}
        {activeTab === TABS.profile && renderProfile()}
      </div>
    </div>
  );
}
