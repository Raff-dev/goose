import { useEffect, useMemo, useState } from 'react';

import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import { useClearTestHistory, useDeleteTestRun, useTestHistory } from '../hooks';
import CodeBlock from './CodeBlock';
import LoadingDots from './LoadingDots';
import MessageCards from './MessageCards';
import SurfaceCard from './SurfaceCard';
import { ToastContainer, useToast } from './Toast';

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
  // Fetch historical results for this test
  const { data: historyResults = [], refetch: refetchHistory } = useTestHistory(test.qualified_name);

  // Mutations for deleting runs
  const deleteRunMutation = useDeleteTestRun();
  const clearTestHistoryMutation = useClearTestHistory();

  // Toast for undo functionality
  const { toasts, showToast, dismissToast } = useToast();

  // Build combined history: historical results + current result (only while test is running)
  const allResults = useMemo(() => {
    // Start with history
    const combined = [...historyResults];

    // Only add current result if test is actively running/queued (live progress)
    // Once test completes (passed/failed), history will be refetched and include it
    const isActivelyRunning = statusProp === 'running' || statusProp === 'queued';
    if (result && isActivelyRunning) {
      const lastHistoryResult = combined[combined.length - 1];
      // Check if the current result is different from the last historical one
      const isDifferent = !lastHistoryResult ||
        lastHistoryResult.duration !== result.duration ||
        lastHistoryResult.passed !== result.passed;
      if (isDifferent) {
        combined.push(result);
      }
    }

    return combined;
  }, [historyResults, result, statusProp]);

  // Store pending deletions for soft delete (undo functionality)
  const [pendingDeletions, setPendingDeletions] = useState<Set<number>>(new Set());

  // Filter out pending deletions from allResults for display
  const visibleResults = useMemo(() => {
    return allResults.filter((_, index) => !pendingDeletions.has(index));
  }, [allResults, pendingDeletions]);

  // History navigation state - default to showing the latest (last in array)
  const [historyIndex, setHistoryIndex] = useState<number>(-1); // -1 means "latest"

  // Reset to latest and clear pending deletions when test changes
  useEffect(() => {
    setHistoryIndex(-1);
    setPendingDeletions(new Set());
  }, [test.qualified_name]);

  // Reset to latest when visible results change
  useEffect(() => {
    setHistoryIndex(-1);
  }, [visibleResults.length]);

  // Compute the actual index and displayed result (using visibleResults)
  const effectiveIndex = historyIndex === -1 ? visibleResults.length - 1 : historyIndex;
  const displayedResult = visibleResults.length > 0 ? visibleResults[effectiveIndex] : result;
  const totalRuns = visibleResults.length;
  const currentRunNumber = totalRuns > 0 ? effectiveIndex + 1 : 0;

  const canGoBack = effectiveIndex > 0;
  const canGoForward = effectiveIndex < totalRuns - 1;

  // Stats: count passed and failed runs (from visible results only)
  const passedCount = useMemo(() => visibleResults.filter(r => r.passed).length, [visibleResults]);
  const failedCount = useMemo(() => visibleResults.filter(r => !r.passed).length, [visibleResults]);

  const handlePrevious = () => {
    if (canGoBack) {
      setHistoryIndex(effectiveIndex - 1);
    }
  };

  const handleNext = () => {
    if (canGoForward) {
      setHistoryIndex(effectiveIndex + 1);
    }
  };

  const handleDeleteCurrentRun = () => {
    if (totalRuns === 0) return;

    // Map from visible index to actual allResults index
    let actualIndex = -1;
    let visibleCount = 0;
    for (let i = 0; i < allResults.length; i++) {
      if (!pendingDeletions.has(i)) {
        if (visibleCount === effectiveIndex) {
          actualIndex = i;
          break;
        }
        visibleCount++;
      }
    }

    if (actualIndex === -1) return;

    // Check if we're trying to delete a run that's actually in history
    const historyLength = historyResults.length;
    if (actualIndex >= historyLength) {
      console.warn('Cannot delete run that is not yet persisted');
      return;
    }

    // Mark as pending deletion (soft delete)
    setPendingDeletions(prev => new Set(prev).add(actualIndex));

    // Navigate to appropriate index after deletion
    const newVisibleCount = visibleResults.length - 1;
    if (newVisibleCount > 0) {
      if (effectiveIndex >= newVisibleCount) {
        setHistoryIndex(newVisibleCount - 1);
      }
    }

    // Show toast with undo and onExpire callbacks
    showToast(
      'Run deleted',
      // onUndo: restore the run (cancel soft delete)
      () => {
        setPendingDeletions(prev => {
          const next = new Set(prev);
          next.delete(actualIndex);
          return next;
        });
      },
      // onExpire: actually delete via API
      async () => {
        try {
          await deleteRunMutation.mutateAsync({
            qualifiedName: test.qualified_name,
            index: actualIndex,
          });
          // Clear from pending and refetch to sync state
          setPendingDeletions(prev => {
            const next = new Set(prev);
            next.delete(actualIndex);
            return next;
          });
          refetchHistory();
        } catch (error) {
          console.error('Failed to delete run:', error);
          // Restore on error
          setPendingDeletions(prev => {
            const next = new Set(prev);
            next.delete(actualIndex);
            return next;
          });
        }
      }
    );
  };

  const handleClearAllHistory = async () => {
    if (totalRuns === 0) return;

    try {
      await clearTestHistoryMutation.mutateAsync(test.qualified_name);
      setHistoryIndex(-1);
      showToast('All executions cleared');
    } catch (error) {
      console.error('Failed to clear history:', error);
    }
  };

  const status = statusProp ?? (displayedResult ? (displayedResult.passed ? 'passed' : 'failed') : 'not-run');
  const statusMeta = STATUS_META[status];
  const isPending = status === 'queued' || status === 'running';
  const durationSeconds = displayedResult?.duration;
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  const [copiedStack, setCopiedStack] = useState(false);

  const stackTrace = useMemo(() => {
    if (!displayedResult?.error) {
      return '';
    }
    if (typeof displayedResult.error === 'string') {
      return displayedResult.error;
    }
    try {
      return JSON.stringify(displayedResult.error, null, 2);
    } catch {
      return String(displayedResult.error);
    }
  }, [displayedResult?.error]);

  useEffect(() => {
    if (!displayedResult) {
      setShowErrorDetails(false);
      return;
    }
    setShowErrorDetails(displayedResult.passed === false);
  }, [displayedResult?.qualified_name, displayedResult?.passed]);

  useEffect(() => {
    if (!copiedStack || typeof window === 'undefined') {
      return;
    }
    const timeout = window.setTimeout(() => setCopiedStack(false), 1500);
    return () => window.clearTimeout(timeout);
  }, [copiedStack]);


  const actualToolCalls = useMemo(() => {
    if (!displayedResult) {
      return [] as string[];
    }
    const messages = (displayedResult.response as any)?.messages;
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
  }, [displayedResult]);

  const expectedToolCalls = displayedResult?.expected_tool_calls ?? [];

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
    const type = displayedResult?.error_type ?? 'unexpected';
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
  }, [displayedResult?.error_type]);

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

  const hasStackTrace = displayedResult?.error_type === 'validation' || displayedResult?.error_type === 'unexpected' || !displayedResult?.error_type;
  const isToolCallError = displayedResult?.error_type === 'tool_call';

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
            {totalRuns > 0 && (
              <div className="flex items-center gap-1 ml-2">
                <button
                  type="button"
                  onClick={handlePrevious}
                  disabled={!canGoBack}
                  className={`p-1 rounded ${canGoBack ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100' : 'text-slate-300 cursor-not-allowed'}`}
                  aria-label="Previous run"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <span className="text-xs font-medium text-slate-500 min-w-[3rem] text-center">
                  {currentRunNumber}/{totalRuns}
                </span>
                <button
                  type="button"
                  onClick={handleNext}
                  disabled={!canGoForward}
                  className={`p-1 rounded ${canGoForward ? 'text-slate-600 hover:text-slate-900 hover:bg-slate-100' : 'text-slate-300 cursor-not-allowed'}`}
                  aria-label="Next run"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
                <button
                  type="button"
                  onClick={handleDeleteCurrentRun}
                  disabled={deleteRunMutation.isPending}
                  className="p-1 ml-1 rounded text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                  aria-label="Delete current run"
                  title="Delete this run"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            )}
          </nav>
          <div className="flex flex-wrap items-center justify-center gap-3">
            {totalRuns > 0 && (
              <div className="flex items-center text-sm font-semibold" title={`${passedCount} passed, ${failedCount} failed`}>
                <span className="text-green-700">{passedCount}</span>
                <span className="text-slate-400 mx-0.5">/</span>
                <span className="text-red-700">{failedCount}</span>
              </div>
            )}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <span className={`inline-flex items-center rounded px-4 py-1.5 text-sm font-semibold ${statusMeta.chip}`}>
                {statusMeta.label}
                {durationSeconds !== undefined && (status === 'passed' || status === 'failed')
                  ? ` (${durationSeconds.toFixed(2)}s)`
                  : ''}
              </span>
            </div>
            {totalRuns > 0 && (
              <button
                type="button"
                onClick={handleClearAllHistory}
                disabled={clearTestHistoryMutation.isPending}
                className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-red-50 hover:text-red-600 transition-colors"
                title="Clear all test executions"
              >
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Clear Executions
              </button>
            )}
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

      {!displayedResult && status === 'not-run' && (
        <SurfaceCard as="section" className="bg-slate-50 p-6 text-base text-slate-600">
          This test has not been executed yet. Trigger a run to capture the latest agent response and validation details.
        </SurfaceCard>
      )}

      {!displayedResult && isPending && (
        <SurfaceCard as="section" className="bg-sky-50/80 p-6" aria-live="polite">
          <div className="flex items-center gap-3 text-sky-900">
            <LoadingDots dotClassName="bg-sky-600" />
            {status === 'queued'
              ? 'Test run queued. Waiting for the runner to start...'
              : 'Test is running. Results will appear here once it finishes.'}
          </div>
        </SurfaceCard>
      )}

      {displayedResult && (
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
                      {(displayedResult.total_tokens ?? 0) > 0 && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-slate-700">
                          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                          </svg>
                          {displayedResult.total_tokens.toLocaleString()} tokens
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
                  {displayedResult.query ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-sm text-slate-800 shadow-inner">
                      <div className="whitespace-pre-wrap">{displayedResult.query}</div>
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
                    {displayedResult.expectations.length === 0 ? (
                      <p className="text-base text-slate-500">No expectations recorded.</p>
                    ) : (
                      <ul className="space-y-2">
                        {(() => {
                          const unmet = new Set(displayedResult.expectations_unmet ?? []);
                          const failureReasons = displayedResult.failure_reasons ?? {};
                          return displayedResult.expectations.map((exp, index) => {
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

          {displayedResult.error && (
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
                    {displayedResult.error_type !== 'tool_call' && (
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
                  {displayedResult.error_type !== 'tool_call' && (
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

          <div className="pt-2">
            {displayedResult.response && Array.isArray((displayedResult.response as any).messages) ? (
              <MessageCards messages={(displayedResult.response as any).messages} />
            ) : (
              <CodeBlock value={displayedResult.response ?? 'No response captured.'} className="text-sm whitespace-pre-wrap" />
            )}
          </div>
        </div>
      )}

      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
