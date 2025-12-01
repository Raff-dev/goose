import { useEffect, useMemo, useState } from 'react';

import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import CodeBlock from './CodeBlock';
import MessageCards from './MessageCards';
import SurfaceCard from './SurfaceCard';

const STATUS_META: Record<TestStatus | 'not-run', { label: string; chip: string }> = {
  passed: {
    label: 'Passed',
    chip: 'bg-green-50 text-green-700',
  },
  failed: {
    label: 'Failed',
    chip: 'bg-red-50 text-red-800',
  },
  queued: {
    label: 'Queued',
    chip: 'bg-yellow-50 text-yellow-700',
  },
  running: {
    label: 'Running',
    chip: 'bg-blue-50 text-blue-700',
  },
  'not-run': {
    label: 'Not Run',
    chip: 'bg-gray-100 text-gray-500',
  },
};

interface TestDetailProps {
  test: TestSummary;
  result?: TestResultModel;
  status?: TestStatus | 'not-run';
  onBack: () => void;
  onRunTest: (testName: string) => void;
}

export function TestDetail({ test, result, status: statusProp, onBack, onRunTest }: TestDetailProps) {
  const status = statusProp ?? (result ? (result.passed ? 'passed' : 'failed') : 'not-run');
  const statusMeta = STATUS_META[status];
  const isPending = status === 'queued' || status === 'running';
  const durationSeconds = result?.duration;
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  useEffect(() => {
    if (
      result?.error_type === 'tool_call' ||
      result?.error_type === 'expectation' ||
      result?.error_type === 'validation'
    ) {
      setShowErrorDetails(true);
      return;
    }
    setShowErrorDetails(false);
  }, [result?.qualified_name, result?.error_type]);

  const actualToolCalls = useMemo(() => {
    if (!result) {
      return [] as string[];
    }
    const messages = (result.response as any)?.messages;
    if (!Array.isArray(messages)) {
      return [] as string[];
    }
    const names: string[] = [];
    for (const message of messages) {
      if (Array.isArray(message?.tool_calls)) {
        for (const call of message.tool_calls) {
          if (call?.name) {
            names.push(call.name);
          }
        }
      }
    }
    return names;
  }, [result]);

  return (
    <div className="space-y-6">
      <SurfaceCard className="sticky top-4 z-10 bg-white/95 px-4 py-3 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-sm text-slate-500 min-w-0">
            <button
              type="button"
              className="inline-flex items-center gap-1 text-slate-600 hover:text-slate-900"
              onClick={onBack}
            >
              <svg className="h-4 w-4 -ml-0.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
              Dashboard
            </button>
            <span aria-hidden="true" className="text-slate-400">/</span>
            <span className="truncate text-slate-900 font-semibold" title={test.name}>{test.name}</span>
          </nav>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <div className="flex flex-wrap items-center justify-center gap-3">
              <span className={`inline-flex items-center rounded px-4 py-1.5 text-sm font-semibold ${statusMeta.chip}`}>
                {statusMeta.label}
                {durationSeconds !== undefined && (status === 'passed' || status === 'failed')
                  ? ` (${durationSeconds.toFixed(2)}s)`
                  : ''}
              </span>
              {result?.error_type && (
                <span className="inline-flex items-center rounded-full border border-red-100 bg-red-50 px-4 py-1.5 text-sm font-semibold text-red-800">
                  {result.error_type === 'tool_call'
                    ? 'Tool Call Error'
                    : result.error_type === 'expectation'
                    ? 'Expectation Error'
                    : result.error_type === 'validation'
                    ? 'Validation Error'
                    : 'Unexpected Error'}
                </span>
              )}
            </div>
            <button
              className={`inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold text-white shadow-lg transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 ${isPending ? 'cursor-not-allowed bg-gradient-to-r from-slate-400 to-slate-500 opacity-70' : 'bg-gradient-to-r from-blue-500 to-indigo-500 hover:shadow-xl'}`}
              disabled={isPending}
              onClick={() => onRunTest(test.qualified_name)}
            >
              {isPending && (
                <svg className="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 018 8" />
                </svg>
              )}
              {isPending ? (status === 'queued' ? 'Queued' : 'Running') : 'Run Test'}
            </button>
          </div>
        </div>
        <span className="sr-only" aria-live="polite">{`Test status: ${statusMeta.label}`}</span>
      </SurfaceCard>

      {!result && status === 'not-run' && (
        <SurfaceCard as="section" className="bg-slate-50 p-6 text-base text-slate-600">
          This test has not been executed yet. Trigger a run to capture the latest agent response and validation details.
        </SurfaceCard>
      )}

      {!result && isPending && (
        <SurfaceCard as="section" className="bg-sky-50/80 p-6" aria-live="polite">
          <div className="flex items-center gap-3 text-sky-900">
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 018 8" />
            </svg>
            {status === 'queued'
              ? 'Test run queued. Waiting for the runner to start...'
              : 'Test is running. Results will appear here once it finishes.'}
          </div>
        </SurfaceCard>
      )}

      {result && (
        <div className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-2">
            <SurfaceCard as="section" className="bg-white p-6">
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                    Test Overview
                  </div>
                  <div className="mt-3 space-y-2">
                    <p className="text-lg font-semibold text-slate-900">{test.name}</p>
                    <p className="text-sm font-medium uppercase tracking-wide text-slate-500">{test.module}</p>
                    {test.docstring && <p className="text-base text-slate-600">{test.docstring}</p>}
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                    Prompt
                  </div>
                  <div className="mt-3">
                    {result.query ? (
                      <CodeBlock value={result.query} className="text-sm" />
                    ) : (
                      <p className="text-base text-slate-500">Prompt was not captured for this execution.</p>
                    )}
                  </div>
                </div>
              </div>
            </SurfaceCard>

            <SurfaceCard as="section" className="bg-white p-6">
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                    Expectations
                  </div>
                  <div className="mt-3">
                    {result.expectations.length === 0 ? (
                      <p className="text-base text-slate-500">No expectations recorded.</p>
                    ) : (
                      <ul className="space-y-2">
                        {(() => {
                          const unmet = new Set(result.expectations_unmet ?? []);
                          return result.expectations.map((exp, index) => {
                          const passed = !unmet.has(exp);
                          return (
                            <li
                              key={`${exp}-${index}`}
                              className="flex items-start gap-3 rounded-lg bg-white px-3 py-2 shadow-sm"
                            >
                              <span className={`h-2.5 w-2.5 rounded-full self-center ${passed ? 'bg-emerald-400/80' : 'bg-rose-400/80'}`} />
                              <span className={`text-base ${passed ? 'text-slate-800' : 'text-red-800'}`}>
                                {exp}
                              </span>
                            </li>
                            );
                          });
                        })()}
                      </ul>
                    )}
                  </div>
                </div>

                <div>
                  <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
                    Expected Tool Calls
                  </div>
                  <div className="mt-3">
                    {result.expected_tool_calls.length === 0 ? (
                      <p className="text-base text-slate-500">No specific tool expectations.</p>
                    ) : (
                      <ul className="space-y-2">
                        {result.expected_tool_calls.map((tool) => {
                          const satisfied = actualToolCalls.includes(tool);
                          return (
                            <li key={tool} className="flex items-center gap-3 rounded-lg bg-white px-3 py-2 shadow-sm">
                              <span className={`h-2.5 w-2.5 rounded-full ${satisfied ? 'bg-emerald-400/80' : 'bg-rose-400/80'}`} />
                              <span className={satisfied ? 'text-base text-slate-800' : 'text-base text-red-800'}>{tool}</span>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            </SurfaceCard>
          </div>

          {result.error && (
            <SurfaceCard as="section" className="bg-rose-50/80 p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm font-semibold text-red-800">
                  Error Details
                </div>
                <button
                  type="button"
                  onClick={() => setShowErrorDetails(prev => !prev)}
                  className="inline-flex items-center gap-2 text-xs font-medium text-red-800 hover:text-red-800"
                >
                  {showErrorDetails ? 'Collapse' : 'Expand'}
                  <svg
                    className={`h-3 w-3 transition-transform ${showErrorDetails ? 'rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 9l7 7 7-7" />
                  </svg>
                </button>
              </div>
              {showErrorDetails && (
                <div className="mt-4 rounded-lg bg-white px-4 py-3 text-sm text-red-800 shadow-sm">
                  {result.error_type === 'unexpected' ? (
                    <CodeBlock value={result.error} className="text-sm" />
                  ) : (
                    <div className="whitespace-pre-wrap text-sm">
                      {result.error}
                    </div>
                  )}
                </div>
              )}
            </SurfaceCard>
          )}

          <SurfaceCard as="section" className="bg-white p-6">
            <div className="flex items-center justify-between">
              <div className="text-lg font-semibold text-slate-900">
                Agent Response
              </div>
            </div>
            <div className="mt-4">
              {result.response && Array.isArray((result.response as any).messages) ? (
                <MessageCards messages={(result.response as any).messages} />
              ) : (
                <CodeBlock value={result.response ?? 'No response captured.'} className="text-sm whitespace-pre-wrap" />
              )}
            </div>
          </SurfaceCard>
        </div>
      )}
    </div>
  );
}
