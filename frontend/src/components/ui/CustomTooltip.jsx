/**
 * Custom Tooltip for Recharts
 * Provides professional styling with proper contrast in light and dark modes
 */

export default function CustomTooltip({ active, payload, label, isDark }) {
  if (!active || !payload || payload.length === 0) return null;

  const entries = Array.isArray(payload) ? payload : [payload];

  return (
    <div
      className={`rounded-lg border shadow-lg p-3 ${
        isDark
          ? "bg-gray-900 border-gray-700"
          : "bg-white border-gray-200 shadow-md"
      }`}
      style={{
        backgroundColor: isDark ? "#111827" : "#ffffff",
        borderColor: isDark ? "#374151" : "#e5e7eb",
        boxShadow: isDark
          ? "0 4px 6px rgba(0, 0, 0, 0.3)"
          : "0 4px 6px rgba(0, 0, 0, 0.1)",
      }}
    >
      {label && (
        <p
          className={`font-semibold text-sm mb-1 ${
            isDark ? "text-gray-200" : "text-gray-900"
          }`}
          style={{ color: isDark ? "#e5e7eb" : "#111827" }}
        >
          {label}
        </p>
      )}
      {entries.map((entry, index) => (
        <p
          key={index}
          style={{
            color: entry.color || (isDark ? "#d1d5db" : "#374151"),
            fontSize: "13px",
            fontWeight: 500,
          }}
        >
          {entry.name}:{" "}
          <span style={{ fontWeight: "bold" }}>{entry.value}</span>
        </p>
      ))}
    </div>
  );
}
