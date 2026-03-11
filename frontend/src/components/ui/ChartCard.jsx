/**
 * Reusable Chart Card Component
 * Wraps chart components with consistent styling and title
 */

export default function ChartCard({ title, children, subtitle }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 shadow-sm">
      {title && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      )}
      <div className="w-full overflow-x-auto">{children}</div>
    </div>
  );
}
