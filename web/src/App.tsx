import { useEffect, useMemo, useState } from 'react';
import type { TestResultModel, TestStatus, TestSummary } from './api/types';
import { GlobalError } from './components/GlobalError';
import { RunControls } from './components/RunControls';
import { Summary } from './components/Summary';
import { TestDetail } from './components/TestDetail';
import { TestGrid } from './components/TestGrid';
import { useCreateRun, useRun, useRuns, useTests } from './hooks';

function App() {
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
  // For tests in the active job: show result from active job (if completed) or nothing
  // For tests NOT in the active job: show latest historical result
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
        // Skip if this test is in the active job (we already handled it above)
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

    // Get all test names that have been run recently
    const allTestNames = new Set<string>();
    for (const run of runs) {
      for (const testName of run.tests) {
        allTestNames.add(testName);
      }
    }

    // First, set status based on per-test statuses from jobs (most recent first)
    for (const run of runs) {
      if (run.test_statuses) {
        for (const [testName, status] of Object.entries(run.test_statuses)) {
          if (!map.has(testName)) {
            map.set(testName, status);
          }
        }
      }
    }

    // Then, for tests without status, set from results
    for (const [name, result] of resultsMap) {
      if (!map.has(name)) {
        map.set(name, result.passed ? 'passed' : 'failed');
      }
    }

    // Any test that hasn't been touched should be 'not-run'
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
    // push a navigable URL so browser back/forward works
    try {
      const url = `/tests/${encodeURIComponent(testName)}`;
      window.history.pushState({}, '', url);
    } catch (e) {
      // ignore
    }
    setSelectedTest(testName);
    setView('detail');
  };

  const handleBack = () => {
    // Try to go back in history first so browser back behaves naturally.
    if (window.history.length > 1) {
      window.history.back();
      // also optimistically update UI
      setView('dashboard');
      setSelectedTest(null);
      return;
    }
    setView('dashboard');
    setSelectedTest(null);
  };

  // Sync app state with URL on mount and when user navigates with back/forward
  useEffect(() => {
    const syncFromLocation = () => {
      const path = window.location.pathname || '/';
      const match = path.match(/^\/tests\/(.+)$/);
      if (match) {
        const testName = decodeURIComponent(match[1]);
        setSelectedTest(testName);
        setView('detail');
      } else {
        setSelectedTest(null);
        setView('dashboard');
      }
    };

    // initial sync
    syncFromLocation();

    const onPop = () => syncFromLocation();
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const handleRunTest = async (testName: string) => {
    try {
      await createRunMutation.mutateAsync({ tests: [testName] });
    } catch {
      // Error is captured in createRunMutation.error and displayed via GlobalError
    }
  };

  const handleRunModule = async (moduleName: string, moduleTests: TestSummary[]) => {
    const names = moduleTests.map(test => test.qualified_name);
    if (!names.length) {
      return;
    }
    try {
      await createRunMutation.mutateAsync({ tests: names });
    } catch {
      // Error is captured in createRunMutation.error and displayed via GlobalError
    }
  };

  const handleReloadTests = () => {
    void refetchTests();
  };

  if (testsLoading || runsLoading) {
    return <div>Loading...</div>;
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
  const latestRun = runs[0];

  const isRunning = runs.some(job => job.status === 'running' || job.status === 'queued');

  // Extract error message from any error (handles Axios errors with various response formats)
  const getErrorMessage = (err: unknown): string | null => {
    if (!err) return null;

    // Axios error with response data
    const axiosError = err as {
      response?: {
        status?: number;
        statusText?: string;
        data?: { detail?: string; message?: string } | string;
      };
      message?: string;
    };

    // Try to get detail from response data
    if (axiosError.response?.data) {
      const data = axiosError.response.data;
      if (typeof data === 'string') {
        return data;
      }
      if (data.detail) {
        return data.detail;
      }
      if (data.message) {
        return data.message;
      }
    }

    // Fall back to status text for HTTP errors
    if (axiosError.response?.status) {
      const status = axiosError.response.status;
      const statusText = axiosError.response.statusText || 'Error';
      return `HTTP ${status}: ${statusText}`;
    }

    // Axios network error or other axios error
    if (axiosError.message) {
      return axiosError.message;
    }

    // Standard Error
    if (err instanceof Error) {
      return err.message;
    }

    return 'An unknown error occurred';
  };

  // Combine job errors, mutation errors, and query errors for display
  const currentError = getErrorMessage(testsError) || getErrorMessage(createRunMutation.error) || latestRun?.error || null;

  // Increment errorKey when a new error occurs (even if same message)
  useEffect(() => {
    if (currentError) {
      setErrorKey(k => k + 1);
    }
  }, [testsError, createRunMutation.error, latestRun?.error]);

  const handleRunAll = async () => {
    try {
      await createRunMutation.mutateAsync(undefined);
    } catch {
      // Error is captured in createRunMutation.error and displayed via GlobalError
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8">
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
    </div>
  );
}

export default App;
