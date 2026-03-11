/**
 * App Layout Component
 * Main application layout with fixed sidebar and responsive content area
 */

import Sidebar from "./Sidebar";

export default function AppLayout({ children }) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 ml-64 overflow-auto">
        <div className="min-h-screen">{children}</div>
      </main>
    </div>
  );
}
