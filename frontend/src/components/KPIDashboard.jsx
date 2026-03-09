export default function KPIDashboard({ data }) {
  if (!data) return <div>No KPI data available</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {/* KPI 1: Acceptance Distribution */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-indigo-600">
          📊 Acceptance Distribution
        </h3>
        <div className="space-y-2 text-sm">
          {data.acceptance_distribution &&
            Object.entries(data.acceptance_distribution).map(([key, val]) => (
              <div key={key} className="flex justify-between">
                <span className="capitalize">{key.replace("_", " ")}</span>
                <span className="font-bold text-indigo-600">{val}%</span>
              </div>
            ))}
        </div>
      </div>

      {/* KPI 2: AI Usage vs Autoeficacia */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-emerald-600">
          🔗 AI Usage Correlation
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span>Correlation</span>
            <span className="font-bold text-emerald-600">
              {data.ai_usage_vs_autoeficacia_correlation?.correlation || "N/A"}
            </span>
          </div>
          <div className="flex justify-between">
            <span>P-value</span>
            <span className="font-bold">
              {data.ai_usage_vs_autoeficacia_correlation?.p_value || "N/A"}
            </span>
          </div>
          <div className="text-xs text-slate-600 mt-3">
            {data.ai_usage_vs_autoeficacia_correlation?.insight}
          </div>
        </div>
      </div>

      {/* KPI 3: Dependency Risk */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-amber-600">
          ⚠️ Dependency Risk
        </h3>
        <div className="space-y-2 text-sm">
          {data.dependency_risk_distribution &&
            Object.entries(data.dependency_risk_distribution).map(
              ([key, val]) => (
                <div key={key} className="flex justify-between">
                  <span className="capitalize">{key.replace("_", " ")}</span>
                  <span className="font-bold text-amber-600">{val}%</span>
                </div>
              ),
            )}
        </div>
      </div>

      {/* KPI 4: Department Segmentation */}
      <div className="card lg:col-span-2">
        <h3 className="text-lg font-semibold mb-4 text-blue-600">
          🏢 Department Segmentation
        </h3>
        <div className="space-y-3 text-sm">
          {data.department_segmentation &&
            Object.entries(data.department_segmentation).map(
              ([dept, metrics]) => (
                <div key={dept} className="border-l-4 border-blue-600 pl-3">
                  <p className="font-semibold text-slate-900">{dept}</p>
                  <div className="flex justify-between text-xs text-slate-600">
                    <span>Motivation: {metrics.avg_motivation}</span>
                    <span>Autoeficacia: {metrics.avg_autoeficacia}</span>
                    <span>Count: {metrics.count}</span>
                  </div>
                </div>
              ),
            )}
        </div>
      </div>

      {/* KPI 5: Motivation by AI Usage */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4 text-purple-600">
          💪 Motivation by AI Usage
        </h3>
        <div className="space-y-2 text-sm">
          {data.motivation_by_ai_usage &&
            Object.entries(data.motivation_by_ai_usage).map(
              ([usage, metrics]) => (
                <div key={usage} className="flex justify-between">
                  <span className="capitalize">{usage}</span>
                  <span className="font-bold text-purple-600">
                    {metrics.avg_motivation}
                  </span>
                </div>
              ),
            )}
        </div>
      </div>
    </div>
  );
}
