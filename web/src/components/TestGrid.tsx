
import { useMemo, useState } from 'react';

import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import { TestCard } from './TestCard';

interface TestGridProps {
  tests: TestSummary[];
  resultsMap: Map<string, TestResultModel>;
  statusMap: Map<string, TestStatus | 'not-run'>;
  onlyFailures: boolean;
  onViewDetails: (testName: string) => void;
  onRunTest: (testName: string) => void;
  onRunModule: (moduleName: string, moduleTests: TestSummary[]) => void;
}

export function TestGrid({ tests, resultsMap, statusMap, onlyFailures, onViewDetails, onRunTest, onRunModule }: TestGridProps) {
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
      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No tests match the current filters.</p>
      ) : (
        <div className="space-y-8">
          {[...groupedByModule.entries()].map(([moduleName, moduleTests], index) => {
            const isCollapsed = collapsedModules[moduleName] ?? false;
            const moduleBusy = moduleTests.some(test => {
              const status = statusMap.get(test.qualified_name);
              return status === 'running' || status === 'queued';
            });
            return (
              <div
                key={moduleName}
                className={`pt-4 ${index === 0 ? 'border-t border-transparent' : 'border-t border-slate-200'} `}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => onRunModule(moduleName, moduleTests)}
                      className={`text-blue-500 hover:text-blue-600 disabled:text-blue-300 disabled:hover:text-blue-300 ${moduleBusy ? 'cursor-not-allowed' : ''}`}
                      title="Run file tests"
                      disabled={moduleBusy}
                    >
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                      <span className="sr-only">Run {moduleName}</span>
                    </button>
                    <h3 className="text-base font-semibold">{moduleName}</h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleModule(moduleName)}
                    className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-700"
                    aria-label={`${isCollapsed ? 'Expand' : 'Collapse'} ${moduleName}`}
                  >
                    <svg
                      className="w-3.5 h-3.5 text-slate-500"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      viewBox="0 0 24 24"
                    >
                      {isCollapsed ? (
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                      ) : (
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 9l7 7 7-7" />
                      )}
                    </svg>
                    {isCollapsed ? 'Expand' : 'Collapse'}
                  </button>
                </div>
                <div
                  className={`overflow-hidden transition-[max-height,opacity] duration-200 ease-out ${
                    isCollapsed ? 'max-h-0 opacity-0' : 'max-h-[2000px] opacity-100'
                  }`}
                  aria-hidden={isCollapsed}
                >
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
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
                          detailsHref={`/tests/${encodeURIComponent(test.qualified_name)}`}
                        />
                      );
                    })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
