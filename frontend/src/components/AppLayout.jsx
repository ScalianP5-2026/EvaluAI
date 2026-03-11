/**
 * App Layout Component
 * Main application layout with sidebar and responsive content area
 */

import Sidebar from "./Sidebar";

export default function AppLayout({ children }) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 overflow-auto transition-all duration-300 ml-64">
        <div className="min-h-screen max-w-screen-2xl mx-auto px-4 md:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
