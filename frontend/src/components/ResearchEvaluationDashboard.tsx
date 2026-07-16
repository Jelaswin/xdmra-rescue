import { useEffect, useState } from 'react';
import { api } from '../services/api';

interface MetricRow {
  label: string;
  value: string | number;
  note?: string;
}

interface ComparisonTable {
  headers: string[];
  rows: string[][];
}

function MetricsTable({ metrics, title }: { metrics: MetricRow[]; title: string }) {
  if (!metrics || metrics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-lg font-semibold mb-3 text-slate-700">{title}</h4>
        <p className="text-slate-500 text-sm">No data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-lg font-semibold mb-3 text-slate-700">{title}</h4>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left py-2 text-slate-600 font-medium">Metric</th>
            <th className="text-right py-2 text-slate-600 font-medium">Value</th>
          </tr>
        </thead>
        <tbody>
          {metrics.map((m, i) => (
            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-2 text-slate-700">
                {m.label}
                {m.note && <span className="block text-xs text-slate-400">{m.note}</span>}
              </td>
              <td className="py-2 text-right font-mono font-medium text-slate-900">{m.value}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ComparisonView({ table, title }: { table: ComparisonTable; title: string }) {
  if (!table || !table.headers || table.headers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="text-lg font-semibold mb-3 text-slate-700">{title}</h4>
        <p className="text-slate-500 text-sm">No comparison data available</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-lg font-semibold mb-3 text-slate-700">{title}</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="bg-slate-100">
              {table.headers.map((h, i) => (
                <th key={i} className="py-2 px-3 text-left text-slate-600 font-medium border border-slate-200">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, ri) => (
              <tr key={ri} className="hover:bg-slate-50">
                {row.map((cell, ci) => (
                  <td key={ci} className="py-2 px-3 text-slate-700 border border-slate-200 font-mono text-sm">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ConfusionMatrixView({ matrix, classes }: { matrix: Record<string, number>; classes: string[] }) {
  if (!matrix || Object.keys(matrix).length === 0) {
    return <p className="text-slate-500 text-sm">No confusion matrix data</p>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h4 className="text-lg font-semibold mb-3 text-slate-700">Confusion Matrix</h4>
      <div className="overflow-x-auto">
        <table className="border-collapse text-sm">
          <thead>
            <tr>
              <th className="p-2 text-slate-600 border border-slate-200 bg-slate-50"></th>
              {classes.map(c => (
                <th key={c} className="p-2 text-slate-600 border border-slate-200 bg-slate-50 font-medium">{c}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {classes.map(trueCls => (
              <tr key={trueCls}>
                <td className="p-2 text-slate-600 border border-slate-200 bg-slate-50 font-medium">{trueCls}</td>
                {classes.map(predCls => {
                  const key = `true_${trueCls}_pred_${predCls}`;
                  const val = matrix[key] || 0;
                  const isCorrect = trueCls === predCls;
                  return (
                    <td
                      key={predCls}
                      className={`p-2 text-center border border-slate-200 font-mono ${
                        isCorrect ? val > 0 ? 'bg-emerald-100 text-emerald-800 font-bold' : '' : val > 0 ? 'bg-red-100 text-red-800' : ''
                      }`}
                    >
                      {val}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function ResearchEvaluationDashboard() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedModule, setSelectedModule] = useState<string>('all');
  const [seed, setSeed] = useState(42);
  const [scenarioLimit, setScenarioLimit] = useState<number | ''>('');
  const [experimentId, setExperimentId] = useState<string | null>(null);
  const [experimentStatus, setExperimentStatus] = useState<string | null>(null);

  const [algorithms, setAlgorithms] = useState<any[]>([]);
  const [priorityEval, setPriorityEval] = useState<any | null>(null);
  const [performance, setPerformance] = useState<any | null>(null);
  const [explainability, setExplainability] = useState<any | null>(null);
  const [experimentResults, setExperimentResults] = useState<any | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const algos = await api.getEvaluationAlgorithms();
      setAlgorithms(algos);
    } catch (e: any) {
      console.error('Failed to load algorithms:', e);
    }
  };

  const runExperiment = async () => {
    setLoading(true);
    setError(null);
    setExperimentId(null);
    setExperimentStatus(null);
    setExperimentResults(null);

    try {
      const result = await api.runEvaluationExperiment({
        module: selectedModule,
        seed,
        scenario_limit: scenarioLimit === '' ? undefined : scenarioLimit,
        repeat_count: 1,
      });

      setExperimentId(result.experiment_id);
      setExperimentStatus(result.status);

      const results = await api.getExperimentResults(result.experiment_id);
      setExperimentResults(results);

      const metrics = await api.getExperimentMetrics(result.experiment_id);

      if (selectedModule === 'all' || selectedModule === 'priority') {
        try {
          const pe = await api.getPriorityModelEvaluation();
          setPriorityEval(pe);
        } catch (e) {
          console.error('Priority eval failed:', e);
        }
      }

      if (selectedModule === 'all' || selectedModule === 'performance') {
        try {
          const perf = await api.getPerformanceBenchmark();
          setPerformance(perf);
        } catch (e) {
          console.error('Performance benchmark failed:', e);
        }
      }

      if (selectedModule === 'all' || selectedModule === 'explainability') {
        try {
          const exp = await api.getExplainabilityCoverage();
          setExplainability(exp);
        } catch (e) {
          console.error('Explainability check failed:', e);
        }
      }
    } catch (e: any) {
      setError(e.message || 'Experiment failed');
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (v: any): string => {
    if (v === null || v === undefined) return 'N/A';
    if (typeof v === 'number') {
      if (Math.abs(v) < 100) return v.toFixed(4);
      return v.toFixed(2);
    }
    return String(v);
  };

  const formatPct = (v: any): string => {
    if (v === null || v === undefined) return 'N/A';
    return `${Number(v).toFixed(2)}%`;
  };

  return (
    <div className="space-y-6">
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
        <strong>Synthetic Data Disclaimer:</strong> All evaluation results use synthetic/generated data.
        Results do not reflect real-world disaster response performance. No statistical significance claim is made.
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4 text-slate-700">Experiment Controls</h3>
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">Module</label>
            <select
              value={selectedModule}
              onChange={e => setSelectedModule(e.target.value)}
              className="border border-slate-300 rounded px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All (Full Suite)</option>
              <option value="rescue">Rescue</option>
              <option value="relief">Relief</option>
              <option value="shelter">Shelter</option>
              <option value="priority">Priority Model</option>
              <option value="explainability">Explainability</option>
              <option value="performance">Performance</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">Seed</label>
            <input
              type="number"
              value={seed}
              onChange={e => setSeed(Number(e.target.value))}
              className="border border-slate-300 rounded px-3 py-2 text-sm w-24"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">Scenario Limit</label>
            <input
              type="number"
              value={scenarioLimit}
              onChange={e => setScenarioLimit(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder="All"
              className="border border-slate-300 rounded px-3 py-2 text-sm w-24"
            />
          </div>

          <button
            onClick={runExperiment}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Running...' : 'Run Experiment'}
          </button>
        </div>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">
            {error}
          </div>
        )}

        {experimentId && (
          <div className="mt-4 bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded text-sm">
            Experiment <strong>{experimentId}</strong> {experimentStatus}. Results ready below.
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div>
          <h3 className="text-lg font-semibold mb-3 text-slate-700">Available Algorithms</h3>
          <div className="bg-white rounded-lg shadow divide-y divide-slate-100">
            {algorithms.length === 0 ? (
              <p className="p-4 text-slate-500 text-sm">Loading...</p>
            ) : (
              algorithms.map(algo => (
                <div key={`${algo.module}-${algo.name}`} className="p-3">
                  <span className="inline-block bg-slate-100 text-slate-600 text-xs px-2 py-0.5 rounded mr-2">{algo.module}</span>
                  <span className="font-medium text-slate-800 text-sm">{algo.name}</span>
                  <p className="text-xs text-slate-500 mt-1">{algo.description}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {experimentResults && (
            <>
              {(selectedModule === 'all' || selectedModule === 'rescue') && experimentResults.rescue_comparison && (
                <ComparisonView
                  title="Rescue Allocation Comparison"
                  table={{
                    headers: ['Algorithm', 'Success Rate', 'Mean Distance', 'Skill Match', 'Latency'],
                    rows: Object.entries(experimentResults.rescue_comparison.metrics || {}).map(([algo, metrics]: [string, any]) => [
                      algo,
                      formatPct(metrics?.success_rate_pct),
                      formatValue(metrics?.mean_distance_km) + ' km',
                      formatPct(metrics?.mean_skill_match_pct),
                      formatValue(metrics?.mean_computation_time_ms) + ' ms',
                    ])
                  }}
                />
              )}

              {(selectedModule === 'all' || selectedModule === 'relief') && experimentResults.relief_comparison && (
                <ComparisonView
                  title="Relief Allocation Comparison"
                  table={{
                    headers: ['Algorithm', 'Fulfilment', 'Mean Shortage', 'Warehouses Used', 'Latency'],
                    rows: Object.entries(experimentResults.relief_comparison.metrics || {}).map(([algo, metrics]: [string, any]) => [
                      algo,
                      formatPct(metrics?.mean_fulfilment_pct),
                      formatValue(metrics?.mean_shortage),
                      formatValue(metrics?.mean_warehouses_used),
                      formatValue(metrics?.mean_computation_time_ms) + ' ms',
                    ])
                  }}
                />
              )}

              {(selectedModule === 'all' || selectedModule === 'shelter') && experimentResults.shelter_comparison && (
                <ComparisonView
                  title="Shelter Allocation Comparison"
                  table={{
                    headers: ['Algorithm', 'Coverage', 'Uncovered', 'Overcrowding', 'Latency'],
                    rows: Object.entries(experimentResults.shelter_comparison.metrics || {}).map(([algo, metrics]: [string, any]) => [
                      algo,
                      formatPct(metrics?.mean_population_coverage_pct),
                      formatValue(metrics?.mean_uncovered_people),
                      formatValue(metrics?.overcrowding_violation_count),
                      formatValue(metrics?.mean_computation_time_ms) + ' ms',
                    ])
                  }}
                />
              )}
            </>
          )}

          {priorityEval && (
            <>
              <MetricsTable
                title="Priority Model Evaluation"
                metrics={[
                  { label: 'Accuracy', value: formatPct(priorityEval.accuracy) },
                  { label: 'Macro Precision', value: formatPct(priorityEval.macro_precision) },
                  { label: 'Macro Recall', value: formatPct(priorityEval.macro_recall) },
                  { label: 'Macro F1', value: formatPct(priorityEval.macro_f1) },
                  { label: 'Weighted F1', value: formatPct(priorityEval.weighted_f1) },
                  { label: 'Training Accuracy', value: formatPct(priorityEval.training_accuracy), note: 'Synthetic data' },
                  { label: 'Evaluation Accuracy', value: formatPct(priorityEval.evaluation_accuracy) },
                  { label: 'Rule-ML Agreement', value: formatPct(priorityEval.rule_ml_agreement_rate) },
                  { label: 'Rule-ML Disagreements', value: priorityEval.rule_ml_disagreement_count },
                  { label: 'Prediction Latency (mean)', value: formatValue(priorityEval.prediction_latency_ms_mean) + ' ms' },
                  { label: 'Prediction Latency (P95)', value: formatValue(priorityEval.prediction_latency_ms_p95) + ' ms' },
                  { label: 'Total Samples', value: priorityEval.total_samples },
                ]}
              />
              {priorityEval.per_class_metrics && Object.keys(priorityEval.per_class_metrics).length > 0 && (
                <ComparisonView
                  title="Per-Class Priority Metrics"
                  table={{
                    headers: ['Class', 'Precision', 'Recall', 'F1 Score', 'Support'],
                    rows: Object.entries(priorityEval.per_class_metrics).map(([cls, m]: [string, any]) => [
                      cls,
                      formatPct(m.precision),
                      formatPct(m.recall),
                      formatPct(m.f1_score),
                      String(m.support),
                    ])
                  }}
                />
              )}
              {priorityEval.confusion_matrix && priorityEval.per_class_metrics && (
                <ConfusionMatrixView
                  matrix={priorityEval.confusion_matrix}
                  classes={Object.keys(priorityEval.per_class_metrics)}
                />
              )}
              {priorityEval.synthetic_data_note && (
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700">
                  {priorityEval.synthetic_data_note}
                  {priorityEval.overfitting_concern_note && <p className="mt-1">{priorityEval.overfitting_concern_note}</p>}
                </div>
              )}
            </>
          )}

          {performance && performance.benchmarks && (
            <MetricsTable
              title="Performance Latency"
              metrics={Object.entries(performance.benchmarks).map(([op, data]: [string, any]) => {
                if (data.error) return { label: op.replace(/_/g, ' '), value: 'Error: ' + data.error };
                return {
                  label: op.replace(/_/g, ' ').replace('latency', '').trim(),
                  value: formatValue(data.mean_ms) + ' ms (median: ' + formatValue(data.median_ms) + ' ms)',
                  note: `P95: ${formatValue(data.p95_ms)} ms, min: ${formatValue(data.min_ms)} ms, max: ${formatValue(data.max_ms)} ms`
                };
              })}
            />
          )}

          {explainability && (
            <MetricsTable
              title="Explainability Coverage"
              metrics={Object.entries(explainability).map(([mod, data]: [string, any]) => ({
                label: `${mod} module`,
                value: formatPct(data.coverage_rate_pct),
                note: `${data.explanation_count} explanations checked`
              }))}
            />
          )}
        </div>
      </div>
    </div>
  );
}