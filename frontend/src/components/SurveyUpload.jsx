import React, { useState, useRef } from "react";
import { dashboardAPI } from "../services/api";


/**
 * Survey Upload Component - Corporate Edition
 *
 * Returns a compact header button that opens a modal for CSV uploads.
 * Maintains all functionality while being visually subtle.
 */
function UploadButton({ onClick, compact }) {
  if (compact) {
    return (
      <button
        onClick={onClick}
        className="w-full px-3 py-2.5 text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 shadow-lg rounded-lg transition-all"
      >
        📥 Subir Datos
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className="px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 dark:bg-blue-600 dark:hover:bg-blue-700 rounded-md transition-colors"
    >
      📥 Subir Datos
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
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
        {children}
      </div>
    </div>
  );
}

const DATASET_OPTIONS = [
  {
    key: "mentors",
    label: "Subir Mentores",
    description: "Carga archivo CSV de mentores",
    accept: ".csv",
  },
  {
    key: "courses",
    label: "Subir Cursos",
    description: "Carga archivo CSV de cursos",
    accept: ".csv",
  },
  {
    key: "employees",
    label: "Subir Empleados",
    description: "Carga archivo Excel de empleados",
    accept: ".xlsx,.xls",
  },
  {
    key: "survey-answers",
    label: "Subir Encuestas",
    description: "Carga archivo Excel/CSV de encuestas",
    accept: ".xlsx,.xls,.csv",
  },
];

function UploadModal({
  selectedOption,
  file,
  isLoading,
  result,
  error,
  isDragging,
  onOptionSelect,
  onFileChange,
  onDragOver,
  onDragLeave,
  onDrop,
  onUpload,
  onButtonClick,
  onReset,
  fileInputRef,
}) {
  return (
    <div className="p-6 space-y-4">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900">Subir Datos</h3>
        <button
          onClick={onReset}
          className="text-gray-400 hover:text-gray-600 text-xl"
          aria-label="Cerrar"
        >
          ×
        </button>
      </div>

      <p className="text-xs text-gray-600">
        Selecciona qué tipo de archivo quieres subir y luego adjunta el archivo.
      </p>

      <div className="grid grid-cols-1 gap-2">
        {DATASET_OPTIONS.map((option) => {
          const active = selectedOption?.key === option.key;
          return (
            <button
              key={option.key}
              onClick={() => onOptionSelect(option)}
              className={`text-left p-3 rounded-md border transition-colors ${
                active
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300 bg-white"
              }`}
            >
              <p className="text-sm font-semibold text-gray-800">{option.label}</p>
              <p className="text-xs text-gray-600 mt-1">{option.description}</p>

              {option.key === "survey-answers" && (
                <p
                  className="mt-2 text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1"
                  title="Dependencia de carga"
                >
                  Recuerda: Debes subir el archivo de Empleados antes de subir las Encuestas.
                </p>
              )}
            </button>
          );
        })}
      </div>

      {selectedOption && (
        <>
          <button
            onClick={onButtonClick}
            disabled={isLoading}
            className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 disabled:bg-gray-400 rounded-md transition-colors"
          >
            {file ? `✓ ${file.name}` : `Seleccionar archivo (${selectedOption.accept})`}
          </button>

          <input
            ref={fileInputRef}
            type="file"
            accept={selectedOption.accept}
            onChange={onFileChange}
            className="hidden"
            disabled={isLoading}
          />

          <div
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            className={`border-2 border-dashed rounded-md p-6 text-center h-28 flex flex-col items-center justify-center cursor-pointer transition-colors ${
              isDragging
                ? "border-blue-500 bg-blue-50"
                : "border-gray-300 bg-gray-50 hover:border-gray-400"
            }`}
          >
            <p className="text-xs text-gray-600">Arrastra un archivo aquí</p>
            <p className="text-xs text-gray-500 mt-1">Máximo 10MB</p>
          </div>
        </>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-xs text-red-700 font-medium">Error: {error}</p>
        </div>
      )}

      {result && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-md space-y-1">
          <p className="text-xs font-semibold text-green-800">{result.message}</p>
          <p className="text-xs text-gray-700">Archivo: {result.filename}</p>
          <p className="text-xs text-gray-700">Tipo: {result.dataset_type}</p>
        </div>
      )}

      <div className="flex gap-2 mt-4">
        <button
          onClick={onUpload}
          disabled={isLoading || !file || !selectedOption}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 rounded-md transition-colors"
        >
          {isLoading ? "Subiendo..." : "Subir"}
        </button>
        <button
          onClick={onReset}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 rounded-md transition-colors"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}

/**
 * Main Component - Exports Header Button + Modal
 */
export default function SurveyUpload({ compact = false }) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  /**
   * Validate file and set it
   */
  const validateAndSetFile = (selectedFile) => {
    if (!selectedOption) {
      setError("Selecciona primero el tipo de carga");
      setFile(null);
      return;
    }

    const acceptedExtensions = selectedOption.accept
      .split(",")
      .map((ext) => ext.trim().toLowerCase());
    const isValidExtension = acceptedExtensions.some((ext) =>
      selectedFile.name.toLowerCase().endsWith(ext)
    );

    if (!isValidExtension) {
      setError(
        `Formato inválido para ${selectedOption.label}. Formatos permitidos: ${selectedOption.accept}`
      );
      setFile(null);
      return;
    }

    const MAX_SIZE = 10 * 1024 * 1024;
    if (selectedFile.size > MAX_SIZE) {
      setError("El archivo debe ser menor de 10MB");
      setFile(null);
      return;
    }

    setFile(selectedFile);
    setError(null);
    setResult(null);
  };

  /**
   * Handle file selection from input
   */
  const handleFileChange = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  };

  /**
   * Handle drag over
   */
  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  /**
   * Handle drag leave
   */
  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  /**
   * Handle drop
   */
  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  };

  /**
   * Trigger file input click
   */
  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleOptionSelect = (option) => {
    setSelectedOption(option);
    setFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  /**
   * Handle file upload
   */
  const handleUpload = async () => {
    if (!selectedOption) {
      setError("Selecciona qué tipo de datos quieres subir");
      return;
    }

    if (!file) {
      setError("Por favor selecciona un archivo primero");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await dashboardAPI.uploadDataset(selectedOption.key, file);
      setResult(data);
      setFile(null);
      setError(null);
    } catch (err) {
      console.error("Upload error:", err);
      const detail = err?.response?.data?.detail;
      setError(
        detail || "Error de conexión. Verifica tu conexión e intenta de nuevo."
      );
      setResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Reset form and close modal
   */
  const handleReset = () => {
    setSelectedOption(null);
    setFile(null);
    setResult(null);
    setError(null);
    setIsModalOpen(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <>
      {/* Header Button */}
      <UploadButton onClick={() => setIsModalOpen(true)} compact={compact} />

      {/* Modal */}
      <ModalOverlay isOpen={isModalOpen} onClose={handleReset}>
        <UploadModal
          selectedOption={selectedOption}
          file={file}
          isLoading={isLoading}
          result={result}
          error={error}
          isDragging={isDragging}
          onOptionSelect={handleOptionSelect}
          onFileChange={handleFileChange}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onUpload={handleUpload}
          onButtonClick={handleButtonClick}
          onReset={handleReset}
          fileInputRef={fileInputRef}
        />
      </ModalOverlay>
    </>
  );
}