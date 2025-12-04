import { useEffect, useMemo, useState } from 'react';

import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import CodeBlock from './CodeBlock';
import LoadingDots from './LoadingDots';
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

const ERROR_TYPE_LABELS: Record<string, string> = {
  tool_call: 'Tool Call Mismatch',
  expectation: 'Expectations Unmet',
  validation: 'Validation Failure',
  unexpected: 'Unexpected Error',
};

const TROUBLESHOOTING_URL = 'https://github.com/Raff-dev/goose/blob/main/README.md';

interface TestDetailProps {
  test: TestSummary;
  result?: TestResultModel;
  status?: TestStatus | 'not-run';
  onBack: () => void;
  onRunTest: (testName: string) => void;
}

export function TestDetail({
  test,
  result,
  status: statusProp,
  onBack,
  onRunTest,
}: TestDetailProps) {
  const status = statusProp ?? (result ? (result.passed ? 'passed' : 'failed') : 'not-run');
  const statusMeta = STATUS_META[status];
  const isPending = status === 'queued' || status === 'running';
  const durationSeconds = result?.duration;
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [copiedStack, setCopiedStack] = useState(false);

  const stackTrace = useMemo(() => {
    if (!result?.error) {
      return '';
    }
    if (typeof result.error === 'string') {
      return result.error;
    }
    try {
      return JSON.stringify(result.error, null, 2);
    } catch {
      return String(result.error);
    }
  }, [result?.error]);

  useEffect(() => {
    if (!result) {
      setShowErrorDetails(false);
      return;
    }
    setShowErrorDetails(result.passed === false);
  }, [result?.qualified_name, result?.passed]);

  useEffect(() => {
    if (!copiedStack || typeof window === 'undefined') {
      return;
    }
    const timeout = window.setTimeout(() => setCopiedStack(false), 1500);
    return () => window.clearTimeout(timeout);
  }, [copiedStack]);


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

  const expectedToolCalls = result?.expected_tool_calls ?? [];

  const extraToolCalls = useMemo(() => {
    if (!actualToolCalls.length) {
      return [] as string[];
    }
    const expectedSet = new Set(expectedToolCalls);
    const extras: string[] = [];
    for (const call of actualToolCalls) {
      if (!expectedSet.has(call)) {
        extras.push(call);
      }
    }
    return Array.from(new Set(extras));
  }, [actualToolCalls, expectedToolCalls]);

  const hasToolExpectationRows = expectedToolCalls.length > 0 || extraToolCalls.length > 0;

  const errorMeta = useMemo(() => {
    const type = result?.error_type ?? 'unexpected';
    const title = ERROR_TYPE_LABELS[type] ?? ERROR_TYPE_LABELS.unexpected;
    if (type === 'expectation') {
      return {
        title,
        tone: 'text-amber-800',
        description: 'One or more expectations did not match the agent response.',
        hint: 'Compare the failing expectation to the agent output and update the assertion or agent prompt.',
        linkLabel: 'Refine expectations',
        linkHref: TROUBLESHOOTING_URL,
      };
    }
    if (type === 'tool_call') {
      return {
        title,
        tone: 'text-red-800',
        description: 'A required tool invocation failed or returned an invalid payload.',
        hint: 'Validate the tool signature and confirm the agent can access the tool from this environment.',
        linkLabel: 'Tooling checklist',
        linkHref: TROUBLESHOOTING_URL,
      };
    }
    if (type === 'validation') {
      return {
        title,
        tone: 'text-red-800',
        description: 'The validation pipeline rejected the run because of schema or policy constraints.',
        hint: 'Review validation rules in your fixtures and ensure the response payload matches the schema.',
        linkLabel: 'Review validation tips',
        linkHref: TROUBLESHOOTING_URL,
      };
    }
    return {
      title,
      tone: 'text-red-800',
      description: 'The runner reported an unhandled exception while executing this test.',
      hint: 'Inspect the stack trace and rerun with debug logging enabled to capture more context.',
      linkLabel: 'Troubleshooting guide',
      linkHref: TROUBLESHOOTING_URL,
    };
  }, [result?.error_type]);

  const handleCopyStack = () => {
    if (!stackTrace) {
      return;
    }
    const text = stackTrace;
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(() => setCopiedStack(true)).catch(() => setCopiedStack(false));
      return;
    }
    try {
      const fallback = document.createElement('textarea');
      fallback.value = text;
      document.body.appendChild(fallback);
      fallback.select();
      document.execCommand('copy');
      document.body.removeChild(fallback);
      setCopiedStack(true);
    } catch {
      setCopiedStack(false);
    }
  };

  const hasStackTrace = result?.error_type === 'validation' || result?.error_type === 'unexpected' || !result?.error_type;
  const isToolCallError = result?.error_type === 'tool_call';

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
            </div>
            <button
              className={`inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-semibold text-white shadow-lg transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-300 ${isPending ? 'cursor-not-allowed bg-gradient-to-r from-slate-400 to-slate-500 opacity-70' : 'bg-blue-500 hover:bg-blue-600 hover:shadow-xl'}`}
              disabled={isPending}
              onClick={() => onRunTest(test.qualified_name)}
            >
              {isPending && <LoadingDots />}
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
            <LoadingDots dotClassName="bg-sky-600" />
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
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Test Overview</p>
                    <div className="flex flex-wrap gap-2 text-xs font-medium text-slate-500">
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {durationSeconds !== undefined ? `${durationSeconds.toFixed(2)}s` : 'Not run'}
                      </span>
                      {(result.total_tokens ?? 0) > 0 && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                          </svg>
                          {result.total_tokens.toLocaleString()} tokens
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3 7h18M3 12h18M3 17h18" />
                        </svg>
                        {test.module}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {test.docstring ? (
                      <p className="text-base text-slate-600">{test.docstring}</p>
                    ) : (
                      <p className="text-base text-slate-600">No description available for this test.</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Prompt</p>
                  {result.query ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-sm text-slate-800 shadow-inner">
                      <div className="whitespace-pre-wrap">{result.query}</div>
                    </div>
                  ) : (
                    <p className="text-base text-slate-500">Prompt was not captured for this execution.</p>
                  )}
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
                          const failureReasons = result.failure_reasons ?? {};
                          return result.expectations.map((exp, index) => {
                          const passed = !unmet.has(exp);
                          const failureReason = failureReasons[exp];
                          const dotColor = passed ? (isToolCallError ? 'bg-slate-300' : 'bg-emerald-400/80') : 'bg-rose-400/80';
                          return (
                            <li
                              key={`${exp}-${index}`}
                              className="flex items-start gap-3 rounded-lg bg-white px-3 py-2 shadow-sm"
                            >
                              <span className={`h-2.5 w-2.5 rounded-full self-center shrink-0 ${dotColor}`} />
                              <div className="flex flex-col gap-1">
                                <span className={`text-base ${passed ? 'text-slate-800' : 'text-red-800'}`}>
                                  {exp}
                                </span>
                                {failureReason && (
                                  <span className="text-sm text-slate-500">
                                    {failureReason}
                                  </span>
                                )}
                              </div>
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
                    {!hasToolExpectationRows ? (
                      <p className="text-base text-slate-500">No specific tool expectations.</p>
                    ) : (
                      <ul className="space-y-2">
                        {expectedToolCalls.map((tool) => {
                          const satisfied = actualToolCalls.includes(tool);
                          const dotColor = satisfied ? 'bg-emerald-400/80' : 'bg-rose-400/80';
                          return (
                            <li key={tool} className="flex items-center gap-3 rounded-lg bg-white px-3 py-2 shadow-sm">
                              <span className={`h-2.5 w-2.5 rounded-full ${dotColor}`} />
                              <span className={satisfied ? 'text-base text-slate-800' : 'text-base text-red-800'}>{tool}</span>
                            </li>
                          );
                        })}
                        {extraToolCalls.map((tool, index) => (
                          <li key={`extra-${tool}-${index}`} className="flex items-center gap-3 rounded-lg bg-white px-3 py-2 shadow-sm">
                            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
                            <div className="flex flex-col">
                              <span className="text-base text-amber-800">{tool}</span>
                              <span className="text-xs font-semibold uppercase tracking-wide text-amber-600">Unexpected tool</span>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            </SurfaceCard>
          </div>

          {result.error && (
            <SurfaceCard as="section" className="bg-white p-0 rounded-r-xl rounded-l-none">
              <div className="border border-red-100 rounded-r-xl rounded-l-none">
                <div className="flex flex-col gap-4 border-l-4 border-red-500 p-6">
                  <div className="flex flex-wrap items-start gap-4">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-red-700" aria-hidden="true">
                      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a1 1 0 00.86 1.5h18.64a1 1 0 00.86-1.5L13.71 3.86a1 1 0 00-1.72 0z" />
                      </svg>
                    </div>
                    <div className="min-w-[200px] flex-1">
                      <p className={`text-lg font-semibold ${errorMeta.tone}`}>{errorMeta.title ?? 'Error'}</p>
                      <p className="mt-1 text-sm text-slate-600">{errorMeta.description}</p>
                    </div>
                    {result.error_type !== 'tool_call' && (
                      <button
                        type="button"
                        onClick={() => setShowErrorDetails(prev => !prev)}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-slate-900"
                        aria-expanded={showErrorDetails}
                      >
                        {showErrorDetails ? 'Hide details' : 'Show details'}
                        <svg
                          className={`h-4 w-4 transition-transform duration-200 ${showErrorDetails ? 'rotate-180' : ''}`}
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 9l7 7 7-7" />
                        </svg>
                      </button>
                    )}
                  </div>
                  <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-700">
                    <div className="font-semibold text-slate-900">Why this failed</div>
                    <p className="mt-1">{errorMeta.hint}</p>
                    <a
                      href={errorMeta.linkHref}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-flex items-center gap-1 text-sm font-semibold text-blue-600 hover:text-blue-700"
                    >
                      {errorMeta.linkLabel}
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M7 17l10-10M7 7h10v10" />
                      </svg>
                    </a>
                  </div>
                  {result.error_type !== 'tool_call' && (
                    <div
                      className={`overflow-hidden transition-all duration-200 ease-in-out ${showErrorDetails ? 'max-h-[640px] opacity-100' : 'max-h-0 opacity-0'}`}
                      aria-hidden={!showErrorDetails}
                    >
                      <div className="mt-4 rounded-lg bg-white px-4 py-3 text-sm text-slate-900 shadow-sm">
                        {hasStackTrace ? (
                          <div className="relative">
                            <button
                              type="button"
                              onClick={handleCopyStack}
                              className="absolute right-3 top-3 inline-flex h-8 w-8 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:text-slate-900"
                              aria-label="Copy stack trace"
                              aria-live="polite"
                            >
                              <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M8 4h9a2 2 0 012 2v11M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h9a2 2 0 002-2m-9-16v3a2 2 0 002 2h3" />
                              </svg>
                            </button>
                            <CodeBlock value={stackTrace} className="max-h-64 overflow-auto pr-12 text-sm" />
                            {copiedStack && (
                              <span className="absolute right-3 top-12 rounded bg-slate-900 px-2 py-0.5 text-xs text-white">Copied</span>
                            )}
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap text-sm text-slate-900">
                            {stackTrace}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </SurfaceCard>
          )}

          <section aria-labelledby="thread-heading" className="pt-2">
            <div className="flex items-center justify-between">
              <div id="thread-heading" className="text-lg font-semibold text-slate-900">
                Thread
              </div>
            </div>
            <div className="mt-4">
              {result.response && Array.isArray((result.response as any).messages) ? (
                <MessageCards messages={(result.response as any).messages} />
              ) : (
                <CodeBlock value={result.response ?? 'No response captured.'} className="text-sm whitespace-pre-wrap" />
              )}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
