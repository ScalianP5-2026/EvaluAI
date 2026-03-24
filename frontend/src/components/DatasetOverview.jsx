/**
 * Dataset Overview Component - Expanded
 * Collapsible section with all descriptive analytics
 *
 * Distribution consistency note:
 *  - Department data sourced from API (department_segmentation, n=100)
 *  - Gender & Primary Tool data sourced from fixed 100-person dataset CSV
 *  - All three distributions share n = 100; percentages computed from same total
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";

// ─── Static dataset constants (survey_raw, n=100) ──────────
// Sorted descending by count so index 0 is always the executive highlight.

const DATASET_N = 100;

const GENDER_DIST = [
  { key: "nonBinary",   count: 29 },
  { key: "female",      count: 27 },
  { key: "unspecified", count: 23 },
  { key: "male",        count: 21 },
];

const TOOL_DIST = [
  { name: "ChatGPT", count: 27 },
  { name: "Copilot", count: 21 },
  { name: "Gemini",  count: 18 },
  { name: "LMS IA",  count: 17 },
  { name: null,      count: 17 }, // localised as dataset.toolOther
];

// ─── Colour palettes ──────────────────────────────────────────────────────────
const DEPT_COLORS   = ["bg-violet-500","bg-indigo-500","bg-blue-500","bg-cyan-500","bg-teal-500"];
const GENDER_COLORS = ["bg-pink-400","bg-rose-500","bg-slate-400","bg-blue-400"];
const TOOL_COLORS   = ["bg-emerald-500","bg-blue-500","bg-indigo-500","bg-amber-500","bg-gray-400"];

// ─── Main component ───────────────────────────────────────────────────────────

export default function DatasetOverview({ data }) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  if (!data || !data.acceptance_distribution) return null;

  try {
    // ── Core totals ────────────────────────────────────────────────────────
    const acceptance = data.acceptance_distribution || {};
    const totalEmployees =
      (acceptance.very_low  ?? 0) +
      (acceptance.low       ?? 0) +
      (acceptance.medium    ?? 0) +
      (acceptance.high      ?? 0) +
      (acceptance.very_high ?? 0);

    const deptData  = data.department_segmentation || {};
    const deptCount = Object.keys(deptData).length;

    const avgMotivation    = 3.95;
    const avgSelfEfficacy  = 3.82;
    const avgAIUsage       = 2.8;
    const avgAge           = 38.5;
    const aiIntegrationLevel = 3.2;

    // ── Dependency risk ────────────────────────────────────────────────────
    const riskData   = data.dependency_risk || {};
    const highRisk   = riskData.high_risk   ?? 0;
    const mediumRisk = riskData.medium_risk ?? 0;
    const lowRisk    = riskData.low_risk    ?? 0;
    const totalRisk  = highRisk + mediumRisk + lowRisk;

    const riskPct = {
      high:   totalRisk > 0 ? Math.round((highRisk   / totalRisk) * 100) : 0,
      medium: totalRisk > 0 ? Math.round((mediumRisk / totalRisk) * 100) : 0,
      low:    totalRisk > 0 ? Math.round((lowRisk    / totalRisk) * 100) : 0,
    };

    // ── Department distribution (API) ──────────────────────────────────────
    // Sorted by headcount descending so index 0 is always top department.
    const deptEntries = Object.entries(deptData)
      .map(([name, v]) => ({ name, count: v.count ?? 0 }))
      .sort((a, b) => b.count - a.count);
    const deptTotal = deptEntries.reduce((s, d) => s + d.count, 0);
    const topDept   = deptEntries[0] ?? { name: "—", count: 0 };
    const topDeptPct = deptTotal > 0 ? Math.round((topDept.count / deptTotal) * 100) : 0;

    // ── AI adoption rate (frequent + very_frequent / motionByUsage total) ─────
    const motionByUsage  = data.motivation_by_usage || {};
    const usageEntries   = Object.entries(motionByUsage);
    const usageTotal     = usageEntries.reduce((s, [, v]) => s + (v.count ?? 0), 0);
    const freqCount      = (motionByUsage["4_frequent"]?.count ?? 0) +
                           (motionByUsage["5_very_frequent"]?.count ?? 0);
    const adoptionRate   = usageTotal > 0 ? Math.round((freqCount / usageTotal) * 100) : 0;

    // ── Automatic insight key selection ────────────────────────────────────────
    const adoptionKey  = adoptionRate < 20 ? "adoptionLow"
                       : adoptionRate < 50 ? "adoptionModerate"
                       :                     "adoptionHigh";
    const motivKey     = avgMotivation  >= 4.0 ? "motivationOk"  : "motivationLow";
    const efficacyKey  = avgSelfEfficacy >= 3.8 ? "selfEfficacyOk" : "selfEfficacyLow";
    const riskInsKey   = riskPct.high > 10 ? "riskAlert" : "riskOk";

    const autoInsights = [
      t(`insights.${adoptionKey}`,  { rate: adoptionRate }),
      t(`insights.${motivKey}`,     { val: avgMotivation }),
      t(`insights.${efficacyKey}`,  { val: avgSelfEfficacy }),
      t("insights.topDept",         { dept: topDept.name,
          val: deptEntries[0] ? (deptData[deptEntries[0].name]?.avg_motivation?.toFixed(2) ?? "—") : "—" }),
      t(`insights.${riskInsKey}`,   { pct: riskPct.high }),
    ];

    // ── Gender distribution (dataset constant, n=100) ──────────────────────
    const genderTop    = GENDER_DIST[0];
    const genderTopLbl = t(`dataset.gender_${genderTop.key}`);
    const genderTopPct = Math.round((genderTop.count / DATASET_N) * 100);

    // ── Primary AI Tool distribution (dataset constant, n=100) ────────────
    const toolTop    = TOOL_DIST[0];
    const toolTopLbl = toolTop.name ?? t("dataset.toolOther");
    const toolTopPct = Math.round((toolTop.count / DATASET_N) * 100);

    return (
      <div className="mb-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden shadow-sm">

        {/* ── Accordion header ──────────────────────────────────────────── */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full px-8 py-5 flex items-center justify-between bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 active:bg-gray-100 dark:active:bg-gray-600 transition-colors select-none"
        >
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {t("dataset.overview")}
          </h3>
          <span
            className={`text-gray-600 dark:text-gray-400 transition-transform duration-300 ${
              isOpen ? "rotate-180" : ""
            }`}
          >
            ▼
          </span>
        </button>

        {/* ── Content ───────────────────────────────────────────────────── */}
        {isOpen && (
          <div className="px-8 py-8 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 space-y-8">

            {/* Section 1 – Core Metrics */}
            <div>
              <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-widest mb-4">
                {t("dataset.coreMetrics")}
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                <MetricBox label={t("dataset.totalEmployees")}    value={totalEmployees} />
                <MetricBox label={t("dataset.departmentCount")}   value={deptCount} />
                <MetricBox label={t("dataset.avgMotivation")}     value={`${avgMotivation}/5`} />
                <MetricBox label={t("dataset.avgSelfEfficacy")}   value={`${avgSelfEfficacy}/5`} />
                <MetricBox label={t("dataset.avgAIUsage")}        value={`${avgAIUsage}/5`} />
                <MetricBox label={t("dataset.avgAge")}            value={`${Math.round(avgAge)} ${t("common.years")}`} />
                <MetricBox label={t("dataset.aiIntegrationLevel")} value={`${aiIntegrationLevel}/5`} />
              </div>
            </div>

            {/* Section 2 – Dependency Risk */}
            <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-widest mb-4">
                {t("dataset.riskDistributionNote")}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <RiskMetric label={t("dataset.lowRisk")}    count={lowRisk}    percentage={riskPct.low}    dotColor="bg-green-500" />
                <RiskMetric label={t("dataset.mediumRisk")} count={mediumRisk} percentage={riskPct.medium} dotColor="bg-amber-500" />
                <RiskMetric label={t("dataset.highRisk")}   count={highRisk}   percentage={riskPct.high}   dotColor="bg-red-500" />
              </div>
              <div className="mt-4 flex h-2 gap-0.5 rounded-full overflow-hidden bg-gray-300 dark:bg-gray-700">
                <div className="bg-green-500" style={{ width: `${riskPct.low}%` }} />
                <div className="bg-amber-500" style={{ width: `${riskPct.medium}%` }} />
                <div className="bg-red-500"   style={{ width: `${riskPct.high}%` }} />
              </div>
            </div>

            {/* Section 3 – Behavioral Indicators */}
            <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-widest mb-5">
                {t("dataset.behavioralIndicators")}
              </h4>

              {/* Human-AI preference – qualitative, kept as static locale */}
              <div className="mb-5">
                <InsightBox
                  icon="🎯"
                  label={t("dataset.humanAIPreference")}
                  value={t("dataset.humanAIPreferenceValue")}
                />
              </div>

              {/* Three distribution cards: consistent n=100 throughout */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

                {/* Department — data from API */}
                <DistributionCard
                  icon="🏢"
                  label={t("dataset.departmentDistribution")}
                  topLabel={topDept.name}
                  topCount={topDept.count}
                  topPct={topDeptPct}
                  entries={deptEntries.map((d, i) => ({
                    label: d.name,
                    count: d.count,
                    color: DEPT_COLORS[i % DEPT_COLORS.length],
                  }))}
                  total={deptTotal}
                />

                {/* Gender — data from dataset constant */}
                <DistributionCard
                  icon="👥"
                  label={t("dataset.genderDistribution")}
                  topLabel={genderTopLbl}
                  topCount={genderTop.count}
                  topPct={genderTopPct}
                  entries={GENDER_DIST.map((g, i) => ({
                    label: t(`dataset.gender_${g.key}`),
                    count: g.count,
                    color: GENDER_COLORS[i % GENDER_COLORS.length],
                  }))}
                  total={DATASET_N}
                />

                {/* Primary AI Tool — data from dataset constant */}
                <DistributionCard
                  icon="🛠️"
                  label={t("dataset.primaryAIToolDist")}
                  topLabel={toolTopLbl}
                  topCount={toolTop.count}
                  topPct={toolTopPct}
                  entries={TOOL_DIST.map((tool, i) => ({
                    label: tool.name ?? t("dataset.toolOther"),
                    count: tool.count,
                    color: TOOL_COLORS[i % TOOL_COLORS.length],
                  }))}
                  total={DATASET_N}
                />

              </div>
            </div>

            {/* Section 4 – Automatic Insights */}
            <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-widest mb-4">
                {t("dataset.autoInsightsTitle")}
              </h4>
              <ul className="space-y-0">
                {autoInsights.map((text, i) => (
                  <li key={i} className="flex items-start gap-3 py-2.5 border-l-2 border-gray-200 dark:border-gray-700 pl-4">
                    <span className="mt-0.5 flex-shrink-0 text-gray-400 dark:text-gray-500 text-xs font-mono w-4 leading-5">
                      {i + 1}.
                    </span>
                    <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                      {text}
                    </p>
                  </li>
                ))}
              </ul>
            </div>

            {/* Footer Note */}
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg mt-2">
              <p className="text-xs text-gray-600 dark:text-gray-400">
                <span className="font-semibold">{t("dataset.datasetNotes")}:</span>{" "}
                {totalEmployees} {t("common.participants")} · {deptCount}{" "}
                {t("common.departments")}. {t("dataset.gdprNote")}
              </p>
            </div>

          </div>
        )}
      </div>
    );
  } catch (error) {
    console.error("Error rendering DatasetOverview:", error);
    return null;
  }
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function MetricBox({ label, value }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
      <p className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider mb-2">
        {label}
      </p>
      <p className="text-xl font-bold text-gray-900 dark:text-white text-right">{value}</p>
    </div>
  );
}

function RiskMetric({ label, count, percentage, dotColor }) {
  const { t } = useTranslation();
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <span className={`w-3 h-3 ${dotColor} rounded-full mr-2`}></span>
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
        </div>
        <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">{percentage}%</span>
      </div>
      <p className="text-lg font-bold text-gray-900 dark:text-white">
        {count} {t("common.employees")}
      </p>
    </div>
  );
}

function InsightBox({ icon, label, value }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-2">
        <span className="text-xl">{icon}</span>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider truncate">
            {label}
          </p>
          <p className="text-sm font-medium text-gray-900 dark:text-white">{value}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * DistributionCard — executive highlight + full bar distribution list.
 * topLabel/topCount/topPct are derived from the SAME entries/total below,
 * so the executive line always matches the distribution list.
 */
function DistributionCard({ icon, label, topLabel, topCount, topPct, entries, total }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Header */}
      <div className="flex items-center gap-1.5 mb-3">
        <span className="text-base">{icon}</span>
        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider leading-tight">
          {label}
        </p>
      </div>

      {/* Executive highlight */}
      <p className="text-sm font-semibold text-gray-900 dark:text-white mb-3 leading-snug">
        {topLabel}
        <span className="ml-2 text-gray-500 dark:text-gray-400 font-normal text-xs">
          — {topCount}&nbsp;({topPct}%)
        </span>
      </p>

      {/* Divider */}
      <div className="border-t border-gray-100 dark:border-gray-700 pt-3 flex-1">
        {entries.map(({ label: lbl, count, color }) => (
          <DistributionRow key={lbl} label={lbl} count={count} total={total} barColor={color} />
        ))}
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-right tabular-nums">
          n = {total}
        </p>
      </div>
    </div>
  );
}

function DistributionRow({ label, count, total, barColor = "bg-blue-500" }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="py-1.5">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-xs text-gray-700 dark:text-gray-300 truncate max-w-[55%]">
          {label}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400 tabular-nums shrink-0">
          {count}&nbsp;({pct}%)
        </span>
      </div>
      <div className="h-1.5 w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
