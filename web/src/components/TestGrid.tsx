
import type { TestResultModel, TestSummary } from '../api/types';
import { TestCard } from './TestCard';

interface TestGridProps {
  tests: TestSummary[];
  resultsMap: Map<string, TestResultModel>;
  statusMap: Map<string, string>;
  onlyFailures: boolean;
  onViewDetails: (testName: string) => void;
  onRunTest: (testName: string) => void;
}

export function TestGrid({ tests, resultsMap, statusMap, onlyFailures, onViewDetails, onRunTest }: TestGridProps) {
  const filtered = tests.filter(test => {
    if (!onlyFailures) return true;
    const status = statusMap.get(test.qualified_name) || 'not-run';
    return status === 'failed';
  });
  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold mb-4">Test Suite ({tests.length})</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map(test => {
          const status = (statusMap.get(test.qualified_name) || 'not-run') as 'passed'|'failed'|'queued'|'running'|'not-run';
          const result = resultsMap.get(test.qualified_name);
          return (
            <TestCard
              key={test.qualified_name}
              name={test.name}
              status={status}
              duration={result?.duration}
              error={result?.error ?? undefined}
              onViewDetails={() => onViewDetails(test.qualified_name)}
              onRunTest={() => onRunTest(test.qualified_name)}
            />
          );
        })}
      </div>
    </section>
  );
}
