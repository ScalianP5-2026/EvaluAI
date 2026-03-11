/**
 * SCALIAN Smart Banner Component
 * Subtle corporate branding header with backdrop blur
 */

import { useTranslation } from "react-i18next";

export default function ScalianBanner() {
  const { t } = useTranslation();

  return (
    <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm px-8 py-3 border-b-2 border-red-500 dark:border-red-600 shadow-sm">
      <p className="text-xs font-bold text-gray-900 dark:text-gray-100 tracking-widest uppercase letter-spacing">
        {t("branding.scalian")}
      </p>
    </div>
  );
}
