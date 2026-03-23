import React, { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { dashboardAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";

/**
 * Survey Upload Component - Corporate Edition
 *
 * Returns a compact header button that opens a modal for CSV uploads.
 * Maintains all functionality while being visually subtle.
 */
function UploadButton({ onClick, compact }) {
  const { t } = useTranslation();
  // Use new i18n key for dashboard action
  const label = t("dashboard.uploadSurveys");
  return (
    <button
      onClick={onClick}
      className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md"
    >
      📥 {label}
    </button>
  );
}

/**
 * Modal overlay component
 */
function ModalOverlay({ isOpen, onClose, children }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

/**
 * Upload Modal Content
 */
function UploadModal({
  file,
  isLoading,
  result,
  error,
  isDragging,
  onFileChange,
  onDragOver,
  onDragLeave,
  onDrop,
  onUpload,
  onButtonClick,
  onReset,
  fileInputRef,
}) {
  // Upload Form View
  if (!result) {
    return (
      <div className="p-6 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          {/* Title is readable in both light and dark mode */}
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Importar datos de encuestas
          </h3>
          <button
            onClick={onReset}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ×
          </button>
        </div>

        {/* Upload Button */}
        <button
          onClick={onButtonClick}
          disabled={isLoading}
          className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 disabled:bg-gray-400 rounded-md transition-colors"
        >
          {file
            ? `✓ ${file.name}`
            : t("dashboard.uploadSelectFile", "Select CSV, XLS, XLSX file")}
        </button>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xls,.xlsx"
          onChange={onFileChange}
          className="hidden"
          disabled={isLoading}
        />

        {/* Drag and Drop Zone */}
        <div
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          /* Drag-and-drop zone styled for both light and dark mode */
          className={`border-2 border-dashed rounded-md p-6 text-center h-32 flex flex-col items-center justify-center cursor-pointer transition-colors
            ${isDragging
              ? "border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-slate-800"
              : "border-gray-300 bg-gray-50 hover:border-gray-400 dark:border-gray-600 dark:bg-slate-900 dark:hover:border-blue-400"
            }
          `}
        >
          <svg
            className="w-8 h-8 text-gray-400 mx-auto mb-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3v-7"
            />
          </svg>
          <p className="text-xs text-gray-600">Arrastra un archivo aquí</p>
          <p className="text-xs text-gray-500 mt-1">Máximo 5MB</p>
        </div>

        {/* Action Buttons */}
        {file && (
          <div className="flex gap-2 mt-4">
            <button
              onClick={onUpload}
              disabled={isLoading}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 rounded-md transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <span className="inline-block animate-spin text-sm">◌</span>
                  Subiendo...
                </>
              ) : (
                "Subir"
              )}
            </button>
            <button
              onClick={onReset}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 rounded-md transition-colors"
            >
              Cancelar
            </button>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-xs text-red-700 font-medium">
              {t("dashboard.uploadError", "Upload error")}: {error}
            </p>
          </div>
        )}
      </div>
    );
  }

  // Results View
  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Resultado de la importación
        </h3>
        <button
          onClick={onReset}
          className="text-gray-400 hover:text-gray-600 text-xl"
        >
          ×
        </button>
      </div>

      {/* Summary Cards - 2x2 Grid */}
      <div className="grid grid-cols-2 gap-2">
        <div className="bg-green-50 border border-green-200 p-3 rounded-md">
          <p className="text-xs text-gray-600 font-medium">Insertados</p>
          <p className="text-2xl font-bold text-green-600 mt-1">
            {result.inserted_rows}
          </p>
        </div>
        <div className="bg-amber-50 border border-amber-200 p-3 rounded-md">
          <p className="text-xs text-gray-600 font-medium">Duplicados</p>
          <p className="text-2xl font-bold text-amber-600 mt-1">
            {result.skipped_duplicates}
          </p>
        </div>
        <div className="bg-red-50 border border-red-200 p-3 rounded-md">
          <p className="text-xs text-gray-600 font-medium">Inválidos</p>
          <p className="text-2xl font-bold text-red-600 mt-1">
            {result.invalid_rows}
          </p>
        </div>
        <div className="bg-blue-50 border border-blue-200 p-3 rounded-md">
          <p className="text-xs text-gray-600 font-medium">Total</p>
          <p className="text-2xl font-bold text-blue-600 mt-1">
            {result.total_rows}
          </p>
        </div>
      </div>

      {/* Summary Text */}
      <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
        <div className="text-xs text-gray-700 dark:text-gray-200 space-y-1">
          <span className="block font-medium text-green-700">
            ✓ {result.inserted_rows} filas insertadas
          </span>
          {result.skipped_duplicates > 0 && (
            <span className="block text-amber-700">
              ⚠ {result.skipped_duplicates} duplicadas omitidas
            </span>
          )}
          {result.invalid_rows > 0 && (
            <span className="block text-red-700">
              ✗ {result.invalid_rows} filas inválidas
            </span>
          )}
        </div>
      </div>

      {/* Error Details */}
      {result.errors && result.errors.length > 0 && (
        <div className="max-h-32 overflow-y-auto space-y-1">
          <p className="text-xs font-medium text-gray-700 sticky top-0 bg-white">
            Errores (primeros {Math.min(result.errors.length, 5)}):
          </p>
          {result.errors.slice(0, 5).map((err, idx) => (
            <div
              key={idx}
              className="text-xs p-2 bg-red-50 border border-red-200 rounded text-red-700"
            >
              <span className="font-mono font-semibold">Fila {err.row}:</span>{" "}
              {err.error}
            </div>
          ))}
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={onReset}
        className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md transition-colors"
      >
        Cerrar
      </button>
    </div>
  );
}

/**
 * Main Component - Exports Header Button + Modal
 */
export default function SurveyUpload({ compact = false }) {
  const { t } = useTranslation();
  const { isRRHH } = useAuth();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState("");
  const [campaignsLoading, setCampaignsLoading] = useState(false);
  const fileInputRef = useRef(null);

  // Fetch campaigns on modal open
  useEffect(() => {
    if (isModalOpen) {
      setCampaignsLoading(true);
      dashboardAPI
        .getCampaigns()
        .then((data) => setCampaigns(Array.isArray(data) ? data : []))
        .catch(() => setCampaigns([]))
        .finally(() => setCampaignsLoading(false));
    } else {
      setCampaigns([]);
      setSelectedCampaign("");
    }
  }, [isModalOpen]);

  // Only RRHH can see/upload
  if (!isRRHH) return null;

  // --- File logic ---
  const validateAndSetFile = (selectedFile) => {
    const allowed = [".csv", ".xls", ".xlsx"];
    const name = selectedFile.name.toLowerCase();
    if (!allowed.some((ext) => name.endsWith(ext))) {
      setError(
        t("dashboard.uploadFileType", "Please select a CSV, XLS, or XLSX file"),
      );
      setFile(null);
      return;
    }
    const MAX_SIZE = 5 * 1024 * 1024;
    if (selectedFile.size > MAX_SIZE) {
      setError(t("dashboard.uploadMaxSize", "Max 5MB"));
      setFile(null);
      return;
    }
    setFile(selectedFile);
    setError(null);
    setResult(null);
  };
  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) validateAndSetFile(selectedFile);
  };
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) validateAndSetFile(droppedFile);
  };
  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };
  const handleUpload = async () => {
    if (!file) {
      setError(t("dashboard.uploadFileRequired", "Please select a file first"));
      return;
    }
    if (!selectedCampaign) {
      setError(t("dashboard.campaignRequired", "Please select a campaign"));
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await dashboardAPI.uploadSurveys(file, selectedCampaign);
      setResult(data);
      setFile(null);
      setError(null);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || t("dashboard.uploadError", "Upload error"));
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };
  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setIsModalOpen(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // --- UI ---
  return (
    <>
      <UploadButton onClick={() => setIsModalOpen(true)} compact={compact} />
      <ModalOverlay isOpen={isModalOpen} onClose={handleReset}>
        <div className="p-6 space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {t("dashboard.uploadTitle")}
            </h3>
            <button
              onClick={handleReset}
              className="text-gray-400 hover:text-gray-600 text-xl"
            >
              ×
            </button>
          </div>

          {/* Campaign Select */}
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-200 mb-1">
              {t("dashboard.campaignLabel")}
            </label>
            <select
              className="w-full border rounded-md px-3 py-2 text-sm bg-white dark:bg-slate-800 dark:text-gray-100 border-slate-300 dark:border-slate-700"
              value={selectedCampaign}
              onChange={(e) => setSelectedCampaign(e.target.value)}
              disabled={campaignsLoading || isLoading}
            >
              <option value="">
                {campaignsLoading
                  ? t("dashboard.campaignLoading")
                  : campaigns.length === 0
                    ? t("dashboard.noCampaigns")
                    : t("dashboard.campaignPlaceholder")}
              </option>
              {campaigns.map((c) => {
                const name = c.title || c.name || "";
                const label = c.wave ? `${name} (${c.wave})` : name || c.id;
                return (
                  <option key={c.id} value={c.id}>
                    {label}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Upload Button */}
          <button
            onClick={handleButtonClick}
            disabled={isLoading}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 disabled:bg-gray-400 rounded-md transition-colors"
          >
            {file ? `✓ ${file.name}` : t("dashboard.uploadSurveys")}
          </button>

          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xls,.xlsx"
            onChange={handleFileChange}
            className="hidden"
            disabled={isLoading}
          />

          {/* Drag and Drop Zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-md p-6 text-center h-32 flex flex-col items-center justify-center cursor-pointer transition-colors
              ${isDragging
                ? "border-blue-500 bg-blue-50 dark:border-blue-400 dark:bg-slate-800"
                : "border-gray-300 bg-gray-50 hover:border-gray-400 dark:border-gray-600 dark:bg-slate-900 dark:hover:border-blue-400"
              }
            `}
          >
            <svg
              className="w-8 h-8 text-gray-400 mx-auto mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3v-7"
              />
            </svg>
            <p className="text-xs text-gray-600 dark:text-gray-300">{t("dashboard.dragDrop")}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {t("dashboard.uploadMaxSize", "Max 5MB")}
            </p>
          </div>

          {/* Action Buttons */}
          {file && (
            <div className="flex gap-2 mt-4">
              <button
                onClick={handleUpload}
                disabled={isLoading}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 rounded-md transition-colors flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <span className="inline-block animate-spin text-sm">◌</span>
                    {t("dashboard.uploading")}
                  </>
                ) : (
                  t("dashboard.uploadButton", "Upload")
                )}
              </button>
              <button
                onClick={handleReset}
                disabled={isLoading}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 rounded-md transition-colors"
              >
                {t("dashboard.cancel", "Cancel")}
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-xs text-red-700 font-medium">
                {t("dashboard.uploadError", "Upload error")}: {error}
              </p>
            </div>
          )}

          {/* Results View */}
          {result && (
            <div className="mt-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {t("dashboard.uploadResultTitle", "Import Result")}
                </h3>
                <button
                  onClick={handleReset}
                  className="text-gray-400 hover:text-gray-600 text-xl"
                >
                  ×
                </button>
              </div>
              {/* Summary Cards - 2x2 Grid */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-green-50 border border-green-200 p-3 rounded-md">
                  <p className="text-xs text-gray-600 font-medium">
                    {t("dashboard.uploadInserted", "Inserted")}
                  </p>
                  <p className="text-2xl font-bold text-green-600 mt-1">
                    {result.inserted_rows}
                  </p>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-3 rounded-md">
                  <p className="text-xs text-gray-600 font-medium">
                    {t("dashboard.uploadDuplicates", "Duplicates")}
                  </p>
                  <p className="text-2xl font-bold text-amber-600 mt-1">
                    {result.skipped_duplicates}
                  </p>
                </div>
                <div className="bg-red-50 border border-red-200 p-3 rounded-md">
                  <p className="text-xs text-gray-600 font-medium">
                    {t("dashboard.uploadInvalid", "Invalid")}
                  </p>
                  <p className="text-2xl font-bold text-red-600 mt-1">
                    {result.invalid_rows}
                  </p>
                </div>
                <div className="bg-blue-50 border border-blue-200 p-3 rounded-md">
                  <p className="text-xs text-gray-600 font-medium">
                    {t("dashboard.uploadTotal", "Total")}
                  </p>
                  <p className="text-2xl font-bold text-blue-600 mt-1">
                    {result.total_rows}
                  </p>
                </div>
              </div>
              {/* Summary Text */}
              <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                <p className="text-xs text-gray-700 space-y-1">
                  <span className="block font-medium text-green-700">
                    ✓ {result.inserted_rows}{" "}
                    {t("dashboard.uploadInsertedRows", "rows inserted")}
                  </span>
                  {result.skipped_duplicates > 0 && (
                    <span className="block text-amber-700">
                      ⚠ {result.skipped_duplicates}{" "}
                      {t(
                        "dashboard.uploadDuplicatesSkipped",
                        "duplicates skipped",
                      )}
                    </span>
                  )}
                  {result.invalid_rows > 0 && (
                    <span className="block text-red-700">
                      ✗ {result.invalid_rows}{" "}
                      {t("dashboard.uploadInvalidRows", "invalid rows")}
                    </span>
                  )}
                </p>
              </div>
              {/* Error Details */}
              {result.errors && result.errors.length > 0 && (
                <div className="max-h-32 overflow-y-auto space-y-1">
                  <p className="text-xs font-medium text-gray-700 sticky top-0 bg-white">
                    {t("dashboard.uploadErrors", "Errors")} (first{" "}
                    {Math.min(result.errors.length, 5)}):
                  </p>
                  {result.errors.slice(0, 5).map((err, idx) => (
                    <div
                      key={idx}
                      className="text-xs p-2 bg-red-50 border border-red-200 rounded text-red-700"
                    >
                      <span className="font-mono font-semibold">
                        {t("dashboard.uploadRow", "Row")} {err.row}:
                      </span>{" "}
                      {err.error}
                    </div>
                  ))}
                </div>
              )}
              {/* Action Button */}
              <button
                onClick={handleReset}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md transition-colors"
              >
                {t("dashboard.close", "Close")}
              </button>
            </div>
          )}
        </div>
      </ModalOverlay>
    </>
  );
}
