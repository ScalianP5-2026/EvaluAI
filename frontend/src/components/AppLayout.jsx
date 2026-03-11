/**
 * App Layout Component
 * Main application layout with collapsible sidebar and responsive content area
 */

import { useState } from "react";
import Sidebar from "./Sidebar";

export default function AppLayout({ children }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      {/* Fixed Sidebar - Collapsible */}
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onCollapseToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Content Area - Responsive with dynamic margin */}
      <main
        className={`flex-1 overflow-auto transition-all duration-300 ${
          isSidebarCollapsed ? "ml-20" : "ml-64"
        }`}
      >
        <div className="min-h-screen max-w-screen-2xl mx-auto px-4 md:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
}
