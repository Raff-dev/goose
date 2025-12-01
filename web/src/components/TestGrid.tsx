
import { useMemo, useState } from 'react';

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
  const [collapsedModules, setCollapsedModules] = useState<Record<string, boolean>>({});

  const filtered = useMemo(() => {
    return tests.filter(test => {
      if (!onlyFailures) {
        return true;
      }
      const status = statusMap.get(test.qualified_name) || 'not-run';
      return status === 'failed';
    });
  }, [tests, statusMap, onlyFailures]);

  const groupedByModule = useMemo(() => {
    return filtered.reduce((map, test) => {
      const existing = map.get(test.module) ?? [];
      existing.push(test);
      map.set(test.module, existing);
      return map;
    }, new Map<string, TestSummary[]>());
  }, [filtered]);

  const toggleModule = (moduleName: string) => {
    setCollapsedModules(prev => ({
      ...prev,
      [moduleName]: !(prev[moduleName] ?? false),
    }));
  };

  return (
    <section className="mt-8">
      <h2 className="text-lg font-semibold mb-4">Test Suite ({filtered.length})</h2>
      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No tests match the current filters.</p>
      ) : (
        <div className="space-y-8">
          {[...groupedByModule.entries()].map(([moduleName, moduleTests], index) => {
            const isCollapsed = collapsedModules[moduleName] ?? false;
            return (
              <div
                key={moduleName}
                className={`pt-4 ${index === 0 ? 'border-t border-transparent' : 'border-t border-slate-200'} `}
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-base font-semibold">{moduleName}</h3>
                  <button
                    type="button"
                    onClick={() => toggleModule(moduleName)}
                    className="text-sm text-slate-500 hover:text-slate-700"
                  >
                    {isCollapsed ? 'Expand' : 'Collapse'}
                  </button>
                </div>
                {!isCollapsed && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {moduleTests.map(test => {
                      const status = (statusMap.get(test.qualified_name) || 'not-run') as 'passed'|'failed'|'queued'|'running'|'not-run';
                      const result = resultsMap.get(test.qualified_name);
                      return (
                        <TestCard
                          key={test.qualified_name}
                          name={test.name}
                          status={status}
                          duration={result?.duration}
                          error={result?.error ?? undefined}
                          result={result}
                          onViewDetails={() => onViewDetails(test.qualified_name)}
                          onRunTest={() => onRunTest(test.qualified_name)}
                        />
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
