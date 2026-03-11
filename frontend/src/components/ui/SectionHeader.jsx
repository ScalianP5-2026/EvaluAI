/**
 * Section Header Component
 * Consistent header styling for dashboard sections
 */

export default function SectionHeader({ title, description }) {
  return (
    <div className="mb-6">
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
        {title}
      </h2>
      {description && (
        <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">
          {description}
        </p>
      )}
    </div>
  );
}
