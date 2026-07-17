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
  const [exporting, setExporting] = useState<string | null>(null);
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

  const downloadExport = async (format: 'csv' | 'json' | 'markdown' | 'latex') => {
    if (!experimentId) return;
    setExporting(format);
    try {
      const blob = await api.exportExperimentResults(experimentId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `experiment_${experimentId}.${format === 'latex' ? 'tex' : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(`Export (${format}) failed: ${e.message}`);
    } finally {
      setExporting(null);
    }
  };

  const explainabilityElementLabels: Record<string, string> = {
    explanation_exists: 'Explanation present',
    resource_name: 'Resource name',
    distance: 'Distance',
    relevant_factor: 'Relevant factor',
    limitation: 'Limitation',
    route_risk: 'Route risk',
    alternative_comparison: 'Alternative comparison',
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

        {experimentId && (
          <div className="mt-4 flex gap-2 flex-wrap">
            <button
              onClick={() => downloadExport('csv')}
              disabled={exporting === 'csv'}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded disabled:opacity-50"
            >
              {exporting === 'csv' ? 'Exporting...' : 'Download CSV'}
            </button>
            <button
              onClick={() => downloadExport('json')}
              disabled={exporting === 'json'}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded disabled:opacity-50"
            >
              {exporting === 'json' ? 'Exporting...' : 'Download JSON'}
            </button>
            <button
              onClick={() => downloadExport('markdown')}
              disabled={exporting === 'markdown'}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded disabled:opacity-50"
            >
              {exporting === 'markdown' ? 'Exporting...' : 'Download Markdown'}
            </button>
            <button
              onClick={() => downloadExport('latex')}
              disabled={exporting === 'latex'}
              className="text-sm bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded disabled:opacity-50"
            >
              {exporting === 'latex' ? 'Exporting...' : 'Download LaTeX'}
            </button>
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
                    headers: [
                      'Algorithm',
                      'Macro Fulfilment',
                      'Wtd Fulfilment',
                      'Mean Shortage',
                      'Total Shortage',
                      'Full',
                      'Partial',
                      'Failed',
                      'Stock Viol.',
                      'Latency',
                    ],
                    rows: Object.entries(experimentResults.relief_comparison.metrics || {}).map(([algo, metrics]: [string, any]) => [
                      algo,
                      formatPct(metrics?.macro_fulfilment_pct),
                      formatPct(metrics?.weighted_fulfilment_pct),
                      formatValue(metrics?.mean_shortage),
                      formatValue(metrics?.total_shortage),
                      String(metrics?.fully_fulfilled_count ?? 'N/A'),
                      String(metrics?.partial_fulfilment_count ?? 'N/A'),
                      String(metrics?.failed_count ?? 'N/A'),
                      String(metrics?.total_stock_violations ?? '0'),
                      formatValue(metrics?.mean_computation_time_ms) + ' ms',
                    ])
                  }}
                />
              )}

              {(selectedModule === 'all' || selectedModule === 'shelter') && experimentResults.shelter_comparison && (
                <ComparisonView
                  title="Shelter Allocation Comparison"
                  table={{
                    headers: [
                      'Algorithm',
                      'Macro Coverage',
                      'Wtd Coverage',
                      'Mean Uncv.',
                      'Total Uncv.',
                      'Full',
                      'Partial',
                      'Failed',
                      'Crit. Ovc.',
                      'Med %',
                      'Acc %',
                      'Latency',
                    ],
                    rows: Object.entries(experimentResults.shelter_comparison.metrics || {}).map(([algo, metrics]: [string, any]) => [
                      algo,
                      formatPct(metrics?.macro_population_coverage_pct),
                      formatPct(metrics?.weighted_population_coverage_pct),
                      formatValue(metrics?.mean_uncovered_people),
                      formatValue(metrics?.total_uncovered_people),
                      String(metrics?.fully_covered_count ?? 'N/A'),
                      String(metrics?.partial_covered_count ?? 'N/A'),
                      String(metrics?.failed_count ?? 'N/A'),
                      String(metrics?.critical_overcrowding_cases ?? 'N/A'),
                      formatPct(metrics?.medical_requirement_match_pct),
                      formatPct(metrics?.accessibility_requirement_match_pct),
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
                  { label: 'Training Score', value: formatPct(priorityEval.training_accuracy), note: 'Held-out test set accuracy' },
                  { label: 'Evaluation Accuracy', value: formatPct(priorityEval.evaluation_accuracy) },
                  { label: 'Macro F1', value: formatPct(priorityEval.macro_f1) },
                  { label: 'Weighted F1', value: formatPct(priorityEval.weighted_f1) },
                  { label: 'Macro Precision', value: formatPct(priorityEval.macro_precision) },
                  { label: 'Macro Recall', value: formatPct(priorityEval.macro_recall) },
                  { label: 'Dataset Size', value: priorityEval.total_samples },
                  { label: 'Rule-ML Agreement', value: formatPct(priorityEval.rule_ml_agreement_rate) },
                  { label: 'Latency (mean)', value: formatValue(priorityEval.prediction_latency_ms_mean) + ' ms' },
                  { label: 'Latency (median)', value: formatValue(priorityEval.prediction_latency_ms_median) + ' ms' },
                  { label: 'Latency (P95)', value: formatValue(priorityEval.prediction_latency_ms_p95) + ' ms' },
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
                  {priorityEval.overfitting_concern_note && (
                    <p className="mt-1 font-medium">{priorityEval.overfitting_concern_note}</p>
                  )}
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
            <>
              <ComparisonView
                title="Explainability Coverage by Module"
                table={{
                  headers: [
                    'Module',
                    'Explanations',
                    'Checks',
                    'Coverage',
                    'Resource Name',
                    'Distance',
                    'Relevant Factor',
                    'Limitation',
                    'Route Risk',
                    'Alt. Comparison',
                  ],
                  rows: Object.entries(explainability).map(([mod, data]: [string, any]) => [
                    mod,
                    String(data.explanation_count ?? 0),
                    String(data.checked_count ?? 0),
                    formatPct(data.coverage_rate_pct),
                    formatPct(data.element_coverage?.resource_name),
                    formatPct(data.element_coverage?.distance),
                    formatPct(data.element_coverage?.relevant_factor),
                    formatPct(data.element_coverage?.limitation),
                    formatPct(data.element_coverage?.route_risk),
                    formatPct(data.element_coverage?.alternative_comparison),
                  ])
                }}
              />
            </>
          )}
        </div>
      </div>
    </div>
  );
}