/**
 * Executive Summary Component
 * Strategic narrative block for decision makers
 */

import { useTranslation } from "react-i18next";

export default function ExecutiveSummary() {
  const { t, i18n } = useTranslation();

  const locale = i18n.language === "es" ? "es-ES" : "en-GB";
  const formattedDate = new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date());

  return (
    <div className="mb-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 shadow-sm">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
        {t("executive.summaryTitle")}
      </h2>

      <div className="space-y-4 text-gray-700 dark:text-gray-300 leading-relaxed">
        <p className="text-base">{t("executive.summaryParagraph1")}</p>
        <p className="text-base">{t("executive.summaryParagraph2")}</p>
        <p className="text-base">{t("executive.summaryParagraph3")}</p>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-medium">{t("executive.lastUpdated")}:</span>{" "}
          {formattedDate}
        </p>
      </div>
    </div>
  );
}
