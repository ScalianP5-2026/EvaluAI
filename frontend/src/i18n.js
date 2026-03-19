import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import enTranslations from "./locales/en.json";
import esTranslations from "./locales/es.json";

const resources = {
  en: { translation: enTranslations },
  es: { translation: esTranslations },
};

i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem("language") || "es",
  interpolation: {
    escapeValue: false,
  },
});

i18n.on("languageChanged", (lng) => {
  localStorage.setItem("language", lng);
});

export default i18n;
