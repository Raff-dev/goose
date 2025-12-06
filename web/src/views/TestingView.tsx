import { useEffect, useMemo, useState } from 'react';
import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import { GlobalError } from '../components/GlobalError';
import { RunControls } from '../components/RunControls';
import { Summary } from '../components/Summary';
import { TestDetail } from '../components/TestDetail';
import { TestGrid } from '../components/TestGrid';
import { useCreateRun, useRun, useRuns, useTests } from '../hooks';

export function TestingView() {
  const {
    data: tests = [],
    isLoading: testsLoading,
    isFetching: testsFetching,
    refetch: refetchTests,
    error: testsError,
  } = useTests();
  const { data: runs = [], isLoading: runsLoading } = useRuns();
  const createRunMutation = useCreateRun();

  const [view, setView] = useState<'dashboard' | 'detail'>('dashboard');
  const [selectedTest, setSelectedTest] = useState<string | null>(null);
  const [onlyFailures, setOnlyFailures] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [errorKey, setErrorKey] = useState(0);

  const { data: currentJob } = useRun(currentJobId || '', !!currentJobId);

  // Find the most recent active job
  const activeJob = useMemo(() => {
    return runs.find(job => job.status === 'running' || job.status === 'queued');
  }, [runs]);

  // Set of test names currently being run in the active job
  const activeJobTests = useMemo(() => {
    return new Set(activeJob?.tests ?? []);
  }, [activeJob]);

  // Aggregate results for display
  const resultsMap = useMemo(() => {
    const map = new Map<string, TestResultModel>();

    // First, add results from the active job (these take priority for tests being run)
    if (activeJob) {
      for (const result of activeJob.results) {
        map.set(result.qualified_name, result);
      }
    }

    // Then, aggregate historical results for tests NOT in the active job
    const sortedRuns = [...runs].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    for (const run of sortedRuns) {
      for (const result of run.results) {
        if (activeJobTests.has(result.qualified_name)) {
          continue;
        }
        if (!map.has(result.qualified_name)) {
          map.set(result.qualified_name, result);
        }
      }
    }
    return map;
  }, [runs, activeJob, activeJobTests]);

  // Compute status for each test
  const statusMap = useMemo(() => {
    const map = new Map<string, TestStatus | 'not-run'>();

    const allTestNames = new Set<string>();
    for (const run of runs) {
      for (const testName of run.tests) {
        allTestNames.add(testName);
      }
    }

    for (const run of runs) {
      if (run.test_statuses) {
        for (const [testName, status] of Object.entries(run.test_statuses)) {
          if (!map.has(testName)) {
            map.set(testName, status);
          }
        }
      }
    }

    for (const [name, result] of resultsMap) {
      if (!map.has(name)) {
        map.set(name, result.passed ? 'passed' : 'failed');
      }
    }

    for (const testName of allTestNames) {
      if (!map.has(testName)) {
        map.set(testName, 'not-run');
      }
    }

    return map;
  }, [runs, resultsMap]);

  useEffect(() => {
    if (currentJob && (currentJob.status === 'succeeded' || currentJob.status === 'failed')) {
      setCurrentJobId(null);
    }
  }, [currentJob]);

  const handleViewDetails = (testName: string) => {
    try {
      const url = `/testing/tests/${encodeURIComponent(testName)}`;
      window.history.pushState({}, '', url);
    } catch {
      // ignore
    }
    setSelectedTest(testName);
    setView('detail');
  };

  const handleBack = () => {
    if (window.history.length > 1) {
      window.history.back();
      setView('dashboard');
      setSelectedTest(null);
      return;
    }
    try {
      window.history.pushState({}, '', '/testing');
    } catch {
      // ignore
    }
    setView('dashboard');
    setSelectedTest(null);
  };

  // Sync app state with URL on mount and when user navigates with back/forward
  useEffect(() => {
    const syncFromLocation = () => {
      const path = window.location.pathname || '/';
      const match = path.match(/^\/testing\/tests\/(.+)$/);
      if (match) {
        const testName = decodeURIComponent(match[1]);
        setSelectedTest(testName);
        setView('detail');
      } else if (path.startsWith('/testing')) {
        setSelectedTest(null);
        setView('dashboard');
      }
    };

    syncFromLocation();

    const onPop = () => syncFromLocation();
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const handleRunTest = async (testName: string) => {
    try {
      await createRunMutation.mutateAsync({ tests: [testName] });
    } catch {
      // Error captured in mutation
    }
  };

  const handleRunModule = async (_moduleName: string, moduleTests: TestSummary[]) => {
    const names = moduleTests.map(test => test.qualified_name);
    if (!names.length) return;
    try {
      await createRunMutation.mutateAsync({ tests: names });
    } catch {
      // Error captured in mutation
    }
  };

  const handleReloadTests = () => {
    void refetchTests();
  };

  const getErrorMessage = (err: unknown): string | null => {
    if (!err) return null;

    const axiosError = err as {
      response?: {
        status?: number;
        statusText?: string;
        data?: { detail?: string; message?: string } | string;
      };
      message?: string;
    };

    if (axiosError.response?.data) {
      const data = axiosError.response.data;
      if (typeof data === 'string') return data;
      if (data.detail) return data.detail;
      if (data.message) return data.message;
    }

    if (axiosError.response?.status) {
      const status = axiosError.response.status;
      const statusText = axiosError.response.statusText || 'Error';
      return `HTTP ${status}: ${statusText}`;
    }

    if (axiosError.message) return axiosError.message;
    if (err instanceof Error) return err.message;
    return 'An unknown error occurred';
  };

  const latestRun = runs[0];
  const currentError = getErrorMessage(testsError) || getErrorMessage(createRunMutation.error) || latestRun?.error || null;

  useEffect(() => {
    if (currentError) {
      setErrorKey(k => k + 1);
    }
  }, [testsError, createRunMutation.error, latestRun?.error]);

  const handleRunAll = async () => {
    try {
      await createRunMutation.mutateAsync(undefined);
    } catch {
      // Error captured in mutation
    }
  };

  if (testsLoading || runsLoading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  const selectedTestData = tests.find(t => t.qualified_name === selectedTest);
  const rawSelectedResult = selectedTest ? resultsMap.get(selectedTest) : undefined;
  let selectedStatus: TestStatus | 'not-run' = 'not-run';

  if (selectedTest) {
    const statusValue = statusMap.get(selectedTest);
    if (statusValue) {
      selectedStatus = statusValue;
    } else if (rawSelectedResult) {
      selectedStatus = rawSelectedResult.passed ? 'passed' : 'failed';
    }
  }

  const selectedResult = selectedStatus === 'passed' || selectedStatus === 'failed' ? rawSelectedResult : undefined;
  const isRunning = runs.some(job => job.status === 'running' || job.status === 'queued');

  return (
    <>
      <GlobalError error={currentError} errorKey={errorKey} />
      {view === 'dashboard' ? (
        <>
          <Summary tests={tests} resultsMap={resultsMap} statusMap={statusMap} />
          <RunControls
            tests={tests}
            onlyFailures={onlyFailures}
            onOnlyFailuresChange={setOnlyFailures}
            onRunAll={handleRunAll}
            isRunning={isRunning}
            onReloadTests={handleReloadTests}
            isReloadingTests={testsFetching}
          />
          <TestGrid
            tests={tests}
            resultsMap={resultsMap}
            statusMap={statusMap}
            onlyFailures={onlyFailures}
            onViewDetails={handleViewDetails}
            onRunTest={handleRunTest}
            onRunModule={handleRunModule}
          />
        </>
      ) : selectedTestData ? (
        <TestDetail
          test={selectedTestData}
          result={selectedResult}
          status={selectedStatus}
          onBack={handleBack}
          onRunTest={handleRunTest}
        />
      ) : null}
    </>
  );
}
