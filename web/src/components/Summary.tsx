import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import { SummaryMetricCard } from './SummaryMetricCard';
import SurfaceCard from './SurfaceCard';

interface SummaryProps {
  tests: TestSummary[];
  resultsMap: Map<string, TestResultModel>;
  statusMap: Map<string, TestStatus | 'not-run'>;
}

export function Summary({ tests, resultsMap, statusMap }: SummaryProps) {
  const totalTests = tests.length;
  const executed = resultsMap.size;
  const passed = Array.from(resultsMap.values()).filter(r => r.passed).length;
  const failed = executed - passed;
  const queued = Array.from(statusMap.values()).filter(s => s === 'queued' || s === 'running').length;
  const executionRate = totalTests > 0 ? `${Math.round((executed / totalTests) * 100)}%` : '0%';
  const totalDuration = Array.from(resultsMap.values()).reduce((sum, r) => sum + r.duration, 0);
  const totalTokens = Array.from(resultsMap.values()).reduce((sum, r) => sum + (r.total_tokens ?? 0), 0);
  const formattedDuration = totalDuration > 0 ? `${Math.floor(totalDuration / 60)}m ${Math.floor(totalDuration % 60)}s` : '—';
  const formattedTokens = totalTokens > 0 ? totalTokens.toLocaleString() : '—';
  const overallStatus = failed === 0 ? 'Passed' : 'Failed';

  return (
    <div>
      <div className="text-xl font-bold mb-4">Test Suite Overview</div>
      <div className="grid grid-cols-5 gap-4 mb-4">
        <SummaryMetricCard
          label="Total Tests"
          value={totalTests}
          icon={
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          }
          status="default"
        />
        <SummaryMetricCard
          label="Executed"
          value={executed}
          icon={
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          status="default"
        />
        <SummaryMetricCard
          label="Queued"
          value={queued}
          icon={
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2" />
            </svg>
          }
          status="warning"
        />
        <SummaryMetricCard
          label="Passed"
          value={passed}
          icon={
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          status="success"
        />
        <SummaryMetricCard
          label="Failed"
          value={failed}
          icon={
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          status="danger"
        />
      </div>
      <SurfaceCard className="bg-white p-4 mb-6">
        <div className="grid grid-cols-4 gap-4">
          <div>
            <div className="font-bold">Last Run Time</div>
            <div>—</div> {/* TODO: compute from runs */}
          </div>
          <div>
            <div className="font-bold">Duration</div>
            <div>{formattedDuration}</div>
          </div>
          <div>
            <div className="font-bold">Tokens</div>
            <div>{formattedTokens}</div>
          </div>
          <div>
            <div className="font-bold">Overall Status</div>
            <div className={`font-bold ${overallStatus === 'Passed' ? 'text-green-500' : 'text-red-800'}`}>
              {overallStatus}
            </div>
          </div>
        </div>
      </SurfaceCard>
    </div>
  );
}
