import { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { TestResultModel, TestStatus, TestSummary } from '../api/types';
import { RunControls } from '../components/RunControls';
import { Summary } from '../components/Summary';
import { TestDetail } from '../components/TestDetail';
import { TestGrid } from '../components/TestGrid';
import { useGlobalError } from '../context/GlobalErrorContext';
import { useCreateRun, useRun, useRuns, useTests } from '../hooks';
import { getErrorMessage } from '../utils/errors';

export function TestingView() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    data: tests = [],
    isLoading: testsLoading,
    isFetching: testsFetching,
    refetch: refetchTests,
    error: testsError,
  } = useTests();
  const { data: runs = [], isLoading: runsLoading } = useRuns();
  const createRunMutation = useCreateRun();

  // Parse view state from URL
  const { view, selectedTest } = useMemo(() => {
    const path = location.pathname;
    const match = path.match(/^\/testing\/tests\/(.+)$/);
    if (match) {
      return { view: 'detail' as const, selectedTest: decodeURIComponent(match[1]) };
    }
    return { view: 'dashboard' as const, selectedTest: null };
  }, [location.pathname]);
  const [onlyFailures, setOnlyFailures] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const { setError } = useGlobalError();

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
    navigate(`/testing/tests/${encodeURIComponent(testName)}`);
  };

  const handleBack = () => {
    navigate('/testing');
  };

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

  const latestRun = runs[0];
  const currentError = getErrorMessage(testsError) || getErrorMessage(createRunMutation.error) || latestRun?.error || null;

  useEffect(() => {
    setError(currentError);
  }, [currentError, setError]);

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
